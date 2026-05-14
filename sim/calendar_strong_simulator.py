"""Strong event-calendar simulator (next-event time advance, entity-level FEL)."""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

from sim.person import Person
from sim.couple import Couple
from sim import tables, random_vars


@dataclass(order=True)
class _Event:
    month: int
    priority: int
    seq: int
    kind: str = field(compare=False)
    a: int | None = field(default=None, compare=False)
    b: int | None = field(default=None, compare=False)


class CalendarStrongSimulator:
    """Independent DES engine using a Future Event List.

    This engine advances to the next pending event and avoids monthly global
    scans over the whole population.
    """

    def __init__(
        self,
        n_women: int,
        n_men: int,
        years: int = 100,
        seed: int | None = None,
        death_mode: str = "monthly",
        pregnancy_mode: str = "range",
    ):
        if seed is not None:
            random_vars.seed(seed)

        self.death_mode = death_mode
        self.pregnancy_mode = pregnancy_mode
        Person._next_id = 0
        Couple._next_id = 0

        self.month = 0
        self.total_months = years * 12

        self.persons: dict[int, Person] = {}
        self.couples: dict[int, Couple] = {}
        self.stats: list[dict] = []

        self._births_this_year = 0
        self._deaths_this_year = 0
        self._couples_formed_this_year = 0
        self._breakups_this_year = 0

        self._queue: list[_Event] = []
        self._seq = 0

        self._born_month: dict[int, int] = {}
        self._available_from: dict[int, int] = {}

        self._init_population(n_women, "F")
        self._init_population(n_men, "M")
        self._bootstrap()

    def _init_population(self, n: int, sex: str) -> None:
        for _ in range(n):
            age_m = random_vars.random_age_initial_months()
            p = Person(sex, age_m)
            self.persons[p.id] = p
            self._born_month[p.id] = -age_m
            self._available_from[p.id] = 0

    def _bootstrap(self) -> None:
        # yearly snapshots
        for yend in range(11, self.total_months, 12):
            self._push(yend, 90, "year_end")

        # initial per-person events
        for p in self.persons.values():
            self._schedule_death(p.id, 0)
            self._schedule_search(p.id, 0)

    def _push(self, month: int, priority: int, kind: str, a: int | None = None, b: int | None = None) -> None:
        if month >= self.total_months:
            return
        self._seq += 1
        heapq.heappush(self._queue, _Event(month, priority, self._seq, kind, a, b))

    def run(self) -> list[dict]:
        while self._queue:
            ev = heapq.heappop(self._queue)
            if ev.month >= self.total_months:
                continue
            self.month = ev.month
            self._dispatch(ev)
        return self.stats

    def _dispatch(self, ev: _Event) -> None:
        if ev.kind == "death":
            self._handle_death(ev.a)
        elif ev.kind == "search":
            self._handle_search(ev.a)
        elif ev.kind == "breakup":
            self._handle_breakup(ev.a, ev.b)
        elif ev.kind == "pregnancy_attempt":
            self._handle_pregnancy_attempt(ev.a, ev.b)
        elif ev.kind == "birth":
            self._handle_birth(ev.a, ev.b)
        elif ev.kind == "solitude_end":
            self._handle_solitude_end(ev.a)
        elif ev.kind == "year_end":
            self._record_stats()
            self._births_this_year = 0
            self._deaths_this_year = 0
            self._couples_formed_this_year = 0
            self._breakups_this_year = 0

    def _age_months(self, person_id: int) -> int:
        return max(0, self.month - self._born_month[person_id])

    def _age_years(self, person_id: int) -> float:
        return self._age_months(person_id) / 12.0

    def _is_available_for_partner(self, p: Person) -> bool:
        return (
            p.alive
            and p.couple_id is None
            and self.month >= self._available_from.get(p.id, 0)
            and self._age_years(p.id) >= 12
        )

    def _schedule_death(self, person_id: int, now: int) -> None:
        p = self.persons.get(person_id)
        if p is None or not p.alive:
            return

        if self.death_mode == "annual":
            # evaluate once per year at year-end using annual probability
            next_year_end = now + (11 - (now % 12))
            if next_year_end < now:
                next_year_end += 12
            self._push(next_year_end, 10, "death", a=person_id)
            return

        age_m = max(0, now - self._born_month[person_id])
        t = now
        ranges = getattr(tables, "_DEATH_RANGES")

        while t < self.total_months:
            age_y = age_m / 12.0
            # current range boundary
            hi = 125
            for lo, hi_i, pm, pf in ranges:
                if age_y < hi_i:
                    hi = hi_i
                    break

            boundary_m = max(1, int(hi * 12 - age_m))
            p_m = tables.death_prob_monthly(age_y, p.sex)
            if p_m <= 0.0:
                return

            u = max(1e-15, random_vars.uniform())
            wait = int(math.ceil(math.log(1.0 - u) / math.log(1.0 - p_m)))
            if wait <= boundary_m:
                self._push(t + wait, 10, "death", a=person_id)
                return

            t += boundary_m
            age_m += boundary_m

    def _kill(self, p: Person) -> None:
        p.alive = False
        p.couple_id = None
        self._deaths_this_year += 1

    def _handle_death(self, person_id: int | None) -> None:
        if person_id is None:
            return
        p = self.persons.get(person_id)
        if p is None or not p.alive:
            return

        age = self._age_years(person_id)
        if self.death_mode == "annual":
            if not random_vars.bernoulli(tables.death_prob_annual(age, p.sex)):
                self._schedule_death(person_id, self.month + 1)
                return

        couple = self._couple_of_person(person_id)
        self._kill(p)

        if couple is not None:
            partner_id = couple.other(person_id)
            partner = self.persons.get(partner_id)
            if couple.id in self.couples:
                del self.couples[couple.id]
            if partner and partner.alive:
                partner.couple_id = None
                self._start_solitude(partner_id)

    def _start_solitude(self, person_id: int) -> None:
        p = self.persons.get(person_id)
        if p is None or not p.alive:
            return
        mean = tables.solitude_mean_months(self._age_years(person_id))
        duration = max(1, int(round(random_vars.exponential(mean))))
        self._available_from[person_id] = self.month + duration
        p.solitude_months_remaining = duration
        self._push(self.month + duration, 40, "solitude_end", a=person_id)

    def _handle_solitude_end(self, person_id: int | None) -> None:
        if person_id is None:
            return
        p = self.persons.get(person_id)
        if p is None or not p.alive:
            return
        p.solitude_months_remaining = 0
        self._schedule_search(person_id, self.month)

    def _schedule_search(self, person_id: int, now: int) -> None:
        p = self.persons.get(person_id)
        if p is None or not p.alive:
            return
        if p.couple_id is not None:
            return
        if self._age_years(person_id) < 12:
            due = self._born_month[person_id] + 12 * 12
            self._push(due, 50, "search", a=person_id)
            return
        due = max(now + 1, self._available_from.get(person_id, 0))
        self._push(due, 50, "search", a=person_id)

    def _handle_search(self, person_id: int | None) -> None:
        if person_id is None:
            return
        seeker = self.persons.get(person_id)
        if seeker is None or not self._is_available_for_partner(seeker):
            if seeker and seeker.alive and seeker.couple_id is None:
                self._schedule_search(person_id, self.month)
            return

        if not random_vars.bernoulli(tables.want_partner_prob(self._age_years(person_id))):
            self._schedule_search(person_id, self.month)
            return

        opposite = "F" if seeker.sex == "M" else "M"
        candidates = [
            p for p in self.persons.values()
            if p.sex == opposite and self._is_available_for_partner(p)
        ]
        random_vars.shuffle(candidates)

        formed = False
        for cand in candidates:
            if not random_vars.bernoulli(tables.want_partner_prob(self._age_years(cand.id))):
                continue
            age_diff = abs(self._age_years(person_id) - self._age_years(cand.id))
            if not random_vars.bernoulli(tables.partner_formation_prob(age_diff)):
                continue

            couple = Couple(person_id, cand.id)
            self.couples[couple.id] = couple
            seeker.couple_id = couple.id
            cand.couple_id = couple.id
            self._couples_formed_this_year += 1

            self._schedule_breakup(couple.id)

            if seeker.sex == "F":
                self._push(self.month + 1, 60, "pregnancy_attempt", a=seeker.id, b=couple.id)
            if cand.sex == "F":
                self._push(self.month + 1, 60, "pregnancy_attempt", a=cand.id, b=couple.id)

            formed = True
            break

        if not formed:
            self._schedule_search(person_id, self.month)

    def _schedule_breakup(self, couple_id: int) -> None:
        p = tables.BREAKUP_PROB_MONTHLY
        u = max(1e-15, random_vars.uniform())
        wait = int(math.ceil(math.log(1.0 - u) / math.log(1.0 - p)))
        self._push(self.month + wait, 30, "breakup", a=couple_id)

    def _handle_breakup(self, couple_id: int | None, _unused: int | None = None) -> None:
        if couple_id is None:
            return
        couple = self.couples.get(couple_id)
        if couple is None:
            return

        pa = self.persons.get(couple.person_a_id)
        pb = self.persons.get(couple.person_b_id)
        del self.couples[couple.id]

        if pa and pa.alive:
            pa.couple_id = None
            self._start_solitude(pa.id)
        if pb and pb.alive:
            pb.couple_id = None
            self._start_solitude(pb.id)

        self._breakups_this_year += 1

    def _handle_pregnancy_attempt(self, woman_id: int | None, couple_id: int | None) -> None:
        if woman_id is None or couple_id is None:
            return
        woman = self.persons.get(woman_id)
        if woman is None or not woman.alive or woman.sex != "F" or woman.pregnant:
            return
        if woman.couple_id != couple_id:
            return

        couple = self.couples.get(couple_id)
        if couple is None:
            return
        partner = self.persons.get(couple.other(woman.id))
        if partner is None or not partner.alive:
            return

        max_desired = max(woman.children_desired, partner.children_desired)
        if woman.children_count >= max_desired:
            return

        prob = tables.pregnancy_prob(self._age_years(woman.id), self.pregnancy_mode)
        if random_vars.bernoulli(prob):
            woman.pregnant = True
            woman.pregnancy_months_remaining = tables.PREGNANCY_DURATION_MONTHS
            due = self.month + tables.PREGNANCY_DURATION_MONTHS
            self._push(due, 70, "birth", a=woman.id, b=couple_id)
            return

        self._push(self.month + 1, 60, "pregnancy_attempt", a=woman.id, b=couple_id)

    def _handle_birth(self, woman_id: int | None, couple_id: int | None) -> None:
        if woman_id is None:
            return
        woman = self.persons.get(woman_id)
        if woman is None or not woman.alive or not woman.pregnant:
            return

        woman.pregnant = False
        woman.pregnancy_months_remaining = 0

        values, cdf = tables.birth_count_cdf()
        n_babies = random_vars.sample_cdf(values, cdf)

        partner = None
        if couple_id is not None:
            couple = self.couples.get(couple_id)
            if couple:
                partner = self.persons.get(couple.other(woman.id))

        birth_year = (self.month + 1) // 12

        for _ in range(n_babies):
            sex = random_vars.random_sex()
            baby = Person(sex, 0)
            baby.mother_id = woman.id
            baby.father_id = partner.id if partner and partner.alive else None
            baby.birth_year = birth_year
            self.persons[baby.id] = baby
            self._born_month[baby.id] = self.month
            self._available_from[baby.id] = self.month + 12 * 12
            self._births_this_year += 1

            self._schedule_death(baby.id, self.month)
            self._schedule_search(baby.id, self.month)

        woman.children_count += n_babies
        if partner and partner.alive:
            partner.children_count += n_babies

        if woman.alive and woman.couple_id is not None:
            self._push(self.month + 1, 60, "pregnancy_attempt", a=woman.id, b=woman.couple_id)

    def _alive(self):
        return (p for p in self.persons.values() if p.alive)

    def _couple_of_person(self, person_id: int) -> Couple | None:
        p = self.persons.get(person_id)
        if p is None or p.couple_id is None:
            return None
        return self.couples.get(p.couple_id)

    def _record_stats(self) -> None:
        alive = list(self._alive())
        year = (self.month + 1) // 12

        men = [p for p in alive if p.sex == "M"]
        women = [p for p in alive if p.sex == "F"]

        ages = [self._age_years(p.id) for p in alive]
        age_groups = {
            "0-12": sum(1 for a in ages if a < 12),
            "12-45": sum(1 for a in ages if 12 <= a < 45),
            "45-76": sum(1 for a in ages if 45 <= a < 76),
            "76+": sum(1 for a in ages if a >= 76),
        }

        for p in alive:
            p.age_months = self._age_months(p.id)
            if p.solitude_months_remaining > 0:
                p.solitude_months_remaining = max(0, self._available_from[p.id] - self.month)

        self.stats.append(
            {
                "year": year,
                "population": len(alive),
                "men": len(men),
                "women": len(women),
                "couples": len(self.couples),
                "single": sum(1 for p in alive if p.is_single),
                "births": self._births_this_year,
                "deaths": self._deaths_this_year,
                "couples_formed": self._couples_formed_this_year,
                "breakups": self._breakups_this_year,
                "age_groups": age_groups,
                "avg_age": sum(ages) / len(ages) if ages else 0,
            }
        )
