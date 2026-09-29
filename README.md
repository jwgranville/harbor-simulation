# `harbor-simulation`

`harbor-simulation` is a message-oriented harbor simulation for systems-integration experiments. It models independently participating vessels and harbor facilities under spatial, temporal, environmental, and shared-resource constraints.

The simulator uses `ropemother` for message-bus interaction while keeping its domain model independent of a particular integration platform. Current capabilities include deterministic simulation time, vessel itineraries and motion, berth authorization and service, terrain and water-depth modeling, under-keel clearance, portable state and event projections, and message-based coordination.

## Resource-conflict scenario

The current baseline includes a deterministic resource-conflict scenario in which berth allocation interacts with safe transit windows. A shallow vessel occupies the shared berth while a deeper inbound vessel has a feasible transit opportunity. The deeper vessel cannot obtain the berth in time to use that opportunity and must wait for the next safe transit window.

`run_resource_conflict_scenario()` executes that scenario and returns immutable projected observations rather than live simulation actors:

```python
from harbor_simulation.scenarios import run_resource_conflict_scenario

result = run_resource_conflict_scenario()

result.docking_events
result.states
result.transit_clearances
```

The result provides docking-event projections, harbor-state snapshots, and transit-clearance projections suitable for downstream analysis or integration without exposing domain object identity.

For message-oriented integration, `publish_resource_conflict_scenario()` in `harbor_simulation.messagebus` runs the same deterministic scenario and publishes its docking-event, harbor-state, and transit-clearance projections through caller-supplied `ropemother` emitters, followed by a `simulation-run-completed` lifecycle projection. The publication boundary depends on the emitter interface rather than a particular bus implementation, so in-process and transport-backed endpoints can consume the same observations without accessing live `harbor-simulation` actors or the scenario result object.

The current transport entry point publishes the completed scenario's immutable observations after the deterministic run; it does not yet stream observations concurrently with scenario execution.

## Development

`harbor-simulation` requires Python 3.13 or later and depends on `ropemother`.
