# Darwin Gödel Machine (DGM) for EvoMap

## Concept

A Darwin Gödel Machine is a self-improving AI system that:
- **Darwin**: Evolves through mutation, selection, and reproduction of Genes
- **Gödel**: Uses formal logic to reason about its own improvement (self-reference)
- **Machine**: An autonomous agent running the evolutionary cycle

In EvoMap context, the DGM is a meta-evolution layer that evolves the *evolution process itself*.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Meta-Loop (Darwin)               │
│  ┌──────────┐  ┌─────────┐  ┌──────────────┐    │
│  │   Genes  │→│ Mutate  │→│  Population  │    │
│  │  (Rules) │  │  /Xover │  │   (Pool)     │    │
│  └──────────┘  └─────────┘  └──────────────┘    │
│         ↓                                      │
│  ┌────────────┐                               │
│  │ Evaluate   │←──────────────────────────────┤
│  │ (Fitness)  │                               │
│  └────────────┘                               │
│         ↓                                      │
│  ┌────────────┐                               │
│  │   Select   │                               │
│  │  (Top-K)   │                               │
│  └────────────┘                               │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│            Gödel Layer (Self-Model)               │
│  - Formal specification of evolution rules        │
│  - Safety invariants: never break protocol        │
│  - Provable bounds on mutation rates, etc.       │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│              Executor (Machine)                   │
│  - Applies selected Genes to actual agent         │
│  - Monitors outcomes, logs to EvolutionEvent     │
│  - Reports fitness delta back to Meta-Loop        │
└─────────────────────────────────────────────────────┘
```

## Core Components

### 1. Gene Representation (Gödel Numbering)

Each Gene is encoded as a natural number via prime factorization:

```
gene_id = 2^(type) * 3^(category) * 5^(strategy_length) * 7^(signals_hash)
```

But practically, we keep JSON as source and compute `asset_id` as SHA256.

### 2. Mutation Operators

- **Add_step**: Insert new strategy step at random position
- **Remove_step**: Remove weakest step (by fitness impact)
- **Modify_signal**: Change one signal to related concept (via embedding similarity)
- **Swap_strategy**: Reorder steps
- **Parameter_tune**: Adjust confidence, blast_radius

Each mutation has a probability `p_mutate` (configurable, default 0.1 per cycle).

### 3. Fitness Function

Fitness score (0.0-1.0) computed from:

- **GDI improvement**: Δgdi_score from previous cycle (weight 0.4)
- **Task success**: Binary if task completed successfully (weight 0.3)
- **Stability**: No errors/quarantine strikes (weight 0.2)
- **Novelty**: Embedding distance from existing population (weight 0.1)

### 4. Selection

Top-κ elitism: Keep top 20% of population unchanged.
Tournament selection for reproduction.

### 5. Reproduction

- **Asexual**: Clone + mutate → new Gene
- **Sexual**: Crossover two high-fitness Genes → child Gene

Reproduced Genes are submitted to Hub as capsule bundles to test fitness.

## Implementation Plan

### Phase 1: Meta-Evolution Loop (v0.1)

- Create `dgm_controller.py` that runs alongside main agent
- Maintains local gene pool in `dgm/pool.jsonl`
- Every N cycles (configurable), triggers meta-evolution:
  1. Evaluate genes in pool (fetch recent outcomes from Hub)
  2. Select top performers
  3. Generate new genes via mutation/crossover
  4. Submit one test capsule using new gene to test fitness

- Configuration: `dgm_config.yaml`
  ```yaml
  pool_size: 100
  cycles_per_meta: 10
  mutation_rate: 0.1
  crossover_rate: 0.2
  selection_pressure: 0.2  # top 20%
  ```

### Phase 2: Formal Safety Invariants

- Encode invariants as Python assertions:
  ```python
  assert gene['category'] in {'repair', 'optimize', 'innovate', 'regulatory'}
  assert len(gene['strategy']) >= 3
  assert all(len(s) >= 15 for s in gene['strategy'])
  assert len(gene['signals_match']) >= 5
  ```
- Before applying any mutation, verify invariants hold post-mutation

- Gödel encoding: generate a unique "proof_id" for each invariant check, storing in `dgm/invariants.json`

### Phase 3: Recursive Self-Improvement

- The DGM controller itself becomes a Gene target
- Meta-meta-evolution: evolve the mutation operators themselves
- Use capsule bundles to propose changes to `dgm_controller.py`
- Must pass "does not break evolution" test (run 3 cycles and compare gdi delta)

## Operation

Add to `AGENTS.md`:

```bash
# Start DGM meta-controller in background
python3 /home/gem/workspace/agent/workspace/dgm_controller.py > logs/dgm.log 2>&1 &
```

## Metrics to Track

- `dgm.fitness.mean` (per generation)
- `dgm.population.diversity` (average pairwise embedding distance)
- `dgm.mutations.applied` (counts by type)
- `dgm.invariant_violations` (should be zero)

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Divergent evolution (non-functional genes) | Hard invariants; reject fitness < 0.5 |
| Overfitting to one task | Diversity bonus in fitness |
| Infinite loops in meta-evolution | Cap generations at 50, reset pool |

## Roadmap

- Week 1: DGM v0.1 (simple mutation + selection)
- Week 2: Integrate fitness evaluation from real Hub
- Week 3: Add crossover and advanced mutations
- Week 4: Safety invariants and formal verification stub
