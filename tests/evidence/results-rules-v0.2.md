# Rules engine vs golden set (rules 0.2.1)

Deterministic layer only: no LLM, no photos. Photo and edge cases are tested in the Claude chat.

| ID | Profile | Expected | Rules engine | Escalate | Coverage | Pass |
|---|---|---|---|---|---|---|
| T01 | lactose + gluten (intolerance) | red | red | no | 7/7 ingredients found in the database | ✅ |
| T02 | gluten (intolerance) | green | green | no | 6/6 ingredients found in the database | ✅ |
| T03 | lactose (intolerance) | yellow | yellow | no | 6/6 ingredients found in the database | ✅ |
| T04 | lactose (intolerance) | green | green | no | 3/3 ingredients found in the database | ✅ |
| T05 | milk allergy (STRICT) | red | red | yes | 3/3 ingredients found in the database | ✅ |
| T06 | celiac (STRICT) | red | red | yes | 5/5 ingredients found in the database | ✅ |
| T07 | celiac (STRICT) | red | red | yes | 4/4 ingredients found in the database | ✅ |
| T08 | lactose (intolerance) | green | green | no | 5/5 ingredients found in the database | ✅ |
| T09 | lactose (intolerance) | red | red | no | 6/6 ingredients found in the database | ✅ |
| T10 | lactose (intolerance) | yellow | yellow | no | 2/2 ingredients found in the database | ✅ |
| T11 | gluten + lactose (intolerance) | green | green | no | 4/4 ingredients found in the database | ✅ |
| T12 | gluten (intolerance) | red | red | no | 5/5 ingredients found in the database | ✅ |
| T13 | celiac (STRICT) | red | red | yes | 4/4 ingredients found in the database | ✅ |
| T14 | lactose (intolerance); user writes in Portuguese | red | red | no | 4/4 ingredients found in the database | ✅ |
| T17 | analyst | escalate | yellow | yes | 4/4 ingredients found in the database | ✅ |
| V01 | vegan (diet) | yellow | yellow | no | 5/5 ingredients found in the database | ✅ |
| V02 | vegan and vegetarian (diet) | red | red | no | 4/4 ingredients found in the database | ✅ |
| V03 | vegan (diet) | red | red | no | 4/4 ingredients found in the database | ✅ |
| V04 | vegetarian (diet) | red | red | no | 6/6 ingredients found in the database | ✅ |
| V05 | vegan (diet) | green | green | no | 4/4 ingredients found in the database | ✅ |
| V06 | vegan and vegetarian (diet) | red | red | no | 11/11 ingredients found in the database | ✅ |
| V07 | vegan (diet) | yellow | yellow | no | 5/5 ingredients found in the database | ✅ |
| V08 | vegan (diet) | yellow | yellow | no | 5/5 ingredients found in the database | ✅ |
| V09 | vegetarian (diet) | yellow | yellow | no | 5/5 ingredients found in the database | ✅ |
| V10 | tree nut allergy (STRICT) + vegan (diet) | red | red | yes | 5/5 ingredients found in the database | ✅ |

**Pass rate: 25/25 (100%)**
