"""Monthly-step discrete-event population simulator."""

from __future__ import annotations
import random

from sim.person import Person
from sim.couple import Couple
from sim import tables, random_vars


class Simulator:
    def __init__(self, n_women: int, n_men: int, years: int = 100, seed: int | None = None):
        if seed is not None:
            random.seed(seed)

        Person._next_id = 0
        Couple._next_id = 0

        self.month: int = 0
        self.total_months: int = years * 12

        self.persons: dict[int, Person] = {}
        self.couples: dict[int, Couple] = {}

        # annual stats snapshots
        self.stats: list[dict] = []

        # counters reset each month for annual aggregation
        self._births_this_year: int = 0
        self._deaths_this_year: int = 0
        self._couples_formed_this_year: int = 0
        self._breakups_this_year: int = 0

        self._init_population(n_women, "F")
        self._init_population(n_men, "M")

    # ── Initialisation ──────────────────────────────────────────────────────

    def _init_population(self, n: int, sex: str) -> None:
        for _ in range(n):
            age_m = random_vars.random_age_initial_months()
            p = Person(sex, age_m)
            self.persons[p.id] = p

    # ── Main loop ───────────────────────────────────────────────────────────

    def run(self) -> list[dict]:
        while self.month < self.total_months:
            self._tick()
            self.month += 1
        return self.stats

    def _tick(self) -> None:
        self._age_everyone()
        self._process_deaths()
        self._process_breakups()
        self._process_solitude()
        self._process_partner_formation()
        self._process_pregnancies()
        self._process_births()

        # record stats at end of each year (month 11, 23, 35, ...)
        if (self.month + 1) % 12 == 0:
            self._record_stats()
            self._births_this_year = 0
            self._deaths_this_year = 0
            self._couples_formed_this_year = 0
            self._breakups_this_year = 0

    # ── Step 1: age everyone ────────────────────────────────────────────────

    def _age_everyone(self) -> None:
        for p in self._alive():
            p.age_months += 1
            if p.pregnant:
                p.pregnancy_months_remaining -= 1

    # ── Step 2: deaths ──────────────────────────────────────────────────────

    def _process_deaths(self) -> None:
        for p in list(self._alive()):
            prob = tables.death_prob_monthly(p.age_years, p.sex)
            if random_vars.bernoulli(prob):
                self._kill(p)

    def _kill(self, p: Person) -> None:
        p.alive = False
        self._deaths_this_year += 1

        if not p.is_single:
            couple = self._couple_of(p)
            if couple:
                partner = self.persons[couple.other(p.id)]
                del self.couples[couple.id]
                partner.partner_id = None
                partner.enter_solitude()

    # ── Step 3: breakups ────────────────────────────────────────────────────

    def _process_breakups(self) -> None:
        for couple in list(self.couples.values()):
            couple.months_together += 1
            if random_vars.bernoulli(tables.BREAKUP_PROB_MONTHLY):
                self._dissolve_couple(couple, widowed=False)

    def _dissolve_couple(self, couple: Couple, *, widowed: bool) -> None:
        pa = self.persons.get(couple.person_a_id)
        pb = self.persons.get(couple.person_b_id)
        del self.couples[couple.id]
        if pa and pa.alive:
            pa.partner_id = None
            pa.enter_solitude()
        if pb and pb.alive:
            pb.partner_id = None
            pb.enter_solitude()
        if not widowed:
            self._breakups_this_year += 1

    # ── Step 4: solitude countdown ──────────────────────────────────────────

    def _process_solitude(self) -> None:
        for p in self._alive():
            if p.solitude_months_remaining > 0:
                p.solitude_months_remaining -= 1

    # ── Step 5: partner formation ───────────────────────────────────────────

    def _process_partner_formation(self) -> None:
        available_men = [
            p for p in self._alive()
            if p.sex == "M" and p.is_available_for_partner
        ]
        available_women = [
            p for p in self._alive()
            if p.sex == "F" and p.is_available_for_partner
        ]

        random_vars.shuffle(available_men)
        random_vars.shuffle(available_women)

        paired_ids: set[int] = set()

        for man in available_men:
            if man.id in paired_ids:
                continue
            for woman in available_women:
                if woman.id in paired_ids:
                    continue

                age_diff = abs(man.age_years - woman.age_years)

                if not random_vars.bernoulli(tables.want_partner_prob(man.age_years)):
                    continue
                if not random_vars.bernoulli(tables.want_partner_prob(woman.age_years)):
                    continue
                if not random_vars.bernoulli(tables.partner_formation_prob(age_diff)):
                    continue

                couple = Couple(man.id, woman.id)
                self.couples[couple.id] = couple
                man.partner_id = couple.id
                woman.partner_id = couple.id

                paired_ids.add(man.id)
                paired_ids.add(woman.id)
                self._couples_formed_this_year += 1
                break

    # ── Step 6: pregnancies ─────────────────────────────────────────────────

    def _process_pregnancies(self) -> None:
        for woman in self._alive():
            if woman.sex != "F":
                continue
            if woman.is_single or woman.pregnant:
                continue

            couple = self._couple_of(woman)
            if couple is None:
                continue

            partner = self.persons.get(couple.other(woman.id))
            if partner is None or not partner.alive:
                continue

            max_desired = max(woman.children_desired, partner.children_desired)
            if woman.children_count >= max_desired:
                continue

            prob = tables.pregnancy_prob(woman.age_years)
            if random_vars.bernoulli(prob):
                woman.pregnant = True
                woman.pregnancy_months_remaining = 9

    # ── Step 7: births ──────────────────────────────────────────────────────

    def _process_births(self) -> None:
        for woman in list(self._alive()):
            if not woman.pregnant:
                continue
            if woman.pregnancy_months_remaining > 0:
                continue

            woman.pregnant = False
            values, cdf = tables.birth_count_cdf()
            n_babies = random_vars.sample_cdf(values, cdf)

            couple = self._couple_of(woman)
            partner = None
            if couple:
                partner = self.persons.get(couple.other(woman.id))

            for _ in range(n_babies):
                sex = random_vars.random_sex()
                baby = Person(sex, 0)
                self.persons[baby.id] = baby
                self._births_this_year += 1

            woman.children_count += n_babies
            if partner and partner.alive:
                partner.children_count += n_babies

    # ── Stats ───────────────────────────────────────────────────────────────

    def _record_stats(self) -> None:
        alive = list(self._alive())
        year = (self.month + 1) // 12

        men   = [p for p in alive if p.sex == "M"]
        women = [p for p in alive if p.sex == "F"]

        ages = [p.age_years for p in alive]
        age_groups = {
            "0-12":   sum(1 for a in ages if a < 12),
            "12-45":  sum(1 for a in ages if 12 <= a < 45),
            "45-76":  sum(1 for a in ages if 45 <= a < 76),
            "76+":    sum(1 for a in ages if a >= 76),
        }

        self.stats.append({
            "year":            year,
            "population":      len(alive),
            "men":             len(men),
            "women":           len(women),
            "couples":         len(self.couples),
            "single":          sum(1 for p in alive if p.is_single),
            "births":          self._births_this_year,
            "deaths":          self._deaths_this_year,
            "couples_formed":  self._couples_formed_this_year,
            "breakups":        self._breakups_this_year,
            "age_groups":      age_groups,
            "avg_age":         sum(ages) / len(ages) if ages else 0,
        })

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _alive(self):
        return (p for p in self.persons.values() if p.alive)

    def _couple_of(self, person: Person) -> Couple | None:
        if person.partner_id is None:
            return None
        return self.couples.get(person.partner_id)
