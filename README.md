"If this system had to handle 10,000 orders per minute, how would you redesign it?"


The Problem With the Current Design

1. The inventory lives in memory:
Products are stored as a plain Python list inside the script.
If two orders arrive at the exact same moment and both check stock
before either one deducts it, both could be approved even if
only enough stock exists for one. This is called a race condition
and it leads to overselling.

2. Everything runs on one machine:
A single Python script running on one computer has a hard limit
on how much work it can do at once. At high volume it would slow
down, queue up, and eventually crash.

3. If it crashes, everything is lost:
There is no record of what happened. No retry mechanism.
A failed order simply disappears.


How I Would Redesign It
I would not rewrite the logic — the core validation rules are correct.
I would change where and how that logic runs.
Here is my thought process, layer by layer.

Layer 1 — Move Inventory to a Real Database
Move stock out of memory into PostgreSQL. Use database locks so two 
orderscan never touch the same product at the same time.
Eliminates overselling.

Layer 2 — Use a Message Queue
Don't process orders the moment they arrive. Put them in a queue (like RabbitMQ)
so the system never gets overwhelmed. If it crashes, the queue still holds
everything — nothing is lost.

Layer 3 — Run Multiple Workers in Parallel

Instead of one script doing all the work, run 50 workers pulling from the queue
simultaneously. Need more speed? Add more workers. Traffic drops? Remove them.
This is horizontal scaling.

Layer 4 — Add a Cache for Product Lookups
Stop reading the database for every single order. Store frequently needed 
data (like product names and prices) in Redis memory. Workers check 
cache first — dramatically faster.

Layer 5 — Separate Validation From Confirmation
Validate instantly and tell the customer "order confirmed." Do the actual stock
deduction in the background. This is exactly how Amazon and every real 
e-commerce site works.

Layer 6 — Observability and Alerting
At this scale you can't watch a terminal.
Log everything, build dashboards, set up automatic alerts when something goes wrong.





Problem-solving

The Situation
A single incoming order needs to be fulfilled across two warehouses.
Neither warehouse alone can fully cover the entire order

Current warehouse stock:
Warehouse A
P1 — Shampoo:5 units
P2 — Soap:10 units

Warehouse B
P1 — Shampoo:10 units
P2 — Soap:5 units

Question 1 — Exact Allocation Plan
Step 1 — Check if any warehouse can fully cover each product on its own

P1 Shampoo needs 8 units
Warehouse A has 5 → not enough 
Warehouse B has 10 → enough 

P2 Soap needs 6 units
Warehouse A has 10 → enough 
Warehouse B has 5 → not enough 

Step 2 — Assign each product to the one warehouse that can fully cover it
This avoids splitting any single product across two warehouses,
which would create two partial shipments of the same item going
to the same customer — messy, confusing, and harder to track.

Step 3 — Final allocation
Warehouse A ships: 6 units of Soap
Warehouse B ships: 8 units of Shampoo
Total shipments: 2 (one from each warehouse)
No single product is split across multiple sources


Question 2 — Strategy Used and Why

Strategy chosen: Minimize shipment splits per product
Out of the available strategies I considered each one carefully:
Minimize total shipments?
Not possible here. Neither warehouse can fulfill the entire order alone.
Warehouse A is short on Shampoo. Warehouse B is short on Soap.
A single-warehouse shipment is simply not an option with this data.

Prioritize fastest delivery?
This would be the right strategy if delivery time data were available.
But the problem provides no information on warehouse locations,
distances, or courier speeds. Making a decision based on data
that does not exist leads to guesswork, not reasoning.

Minimize cost?
Same problem — no shipping cost data is provided.
Without numbers, any cost-based decision would be invented, not calculated.
Minimize splits per product — why this wins
Splitting one product across two warehouses creates real operational pain:
two partial boxes for the same item, two tracking numbers for one product,
a higher chance of the customer receiving half their order first
and not understanding why. By keeping each product whole within
one warehouse, the shipment stays clean, trackable, and simple.
This strategy produces the best possible outcome given the
constraints — 2 shipments, zero product splits, both warehouses
remain stocked, and no invented assumptions were needed to reach it.


Question 3 — Assumptions Made Explicitly
Assumptions that stay hidden are the ones that cause real problems.
Here is everything I assumed, stated clearly.

Assumption 1 — Both warehouses can ship to the same customer
I assumed no geographic restriction prevents either warehouse from
reaching the delivery address. If Warehouse B only serves one region
and the customer is outside it, the entire allocation changes.

Assumption 2 — Shipping cost is equal from both warehouses
No cost data was provided so both warehouses were treated as equal
in cost. In reality the closer warehouse is almost always cheaper.
If cost data were available, I would assign the larger quantity
to the closer warehouse.

Assumption 3 — Delivery speed is equal from both warehouses
No delivery time data was provided. If one warehouse were significantly
faster, I would prioritize it for the larger quantity item so more
of the order reaches the customer sooner.

Assumption 4 — The order must be fully fulfilled
I assumed partial delivery is not acceptable — the customer expects
all 8 Shampoos and all 6 Soaps. If partial fulfillment were allowed,
the strategy and allocation would both change.

Assumption 5 — No restocking is imminent
I assumed we cannot wait for a restock before shipping.
If Warehouse A was due a Shampoo delivery in one hour,
it might make sense to wait and consolidate everything into
one shipment rather than splitting across two warehouses.




Quantitative and logistic reasoning

System Parameters
ParameterValueTime to process one order 2 seconds Orders handled simultaneously 5 (parallel) Timeframe being evaluated1 minute

Q1 — Throughput Calculation
Question: Given the system processes each order in 2 seconds and handles
5 orders simultaneously, how many orders can be processed in 1 minute?
Working:
Step 1 — Convert the timeframe to seconds
         1 minute = 60 seconds

Step 2 — Calculate how many orders ONE worker completes in 60 seconds
         60 seconds ÷ 2 seconds per order = 30 orders per worker

Step 3 — Multiply by the number of parallel workers
         30 orders × 5 workers = 150 orders

Answer: The system can process 150 orders per minute.

Q2 — Overload Scenario
Question: If orders suddenly spike to 300 per minute, what happens
to the system? Describe the effect and the failure mode.
Working:
System capacity  =  150 orders per minute  (from Q1)
Incoming load    =  300 orders per minute
Overflow         =  300 - 150 = 150 orders per minute that cannot be processed
What happens — step by step:
Stage 1 — The queue starts filling up
The system can only handle 150 orders per minute but 300 are arriving.
The extra 150 orders per minute have nowhere to go — they pile up
in the processing queue. Every minute that passes, the backlog
grows by 150 orders.
Stage 2 — Response times slow down
As the queue grows, orders that arrive now have to wait longer
before they even start processing. What used to be instant
starts taking seconds, then minutes. Customers see delays.
Stage 3 — Memory runs out
The queue is stored in memory. With 150 extra orders piling up
every single minute, memory fills up fast. The system starts
struggling to hold everything it has been asked to do.
Stage 4 — System crash (the failure mode)
Eventually memory is exhausted. The system has two options —
both bad. It either crashes completely and loses every order
sitting in the queue, or it starts rejecting new incoming orders
with errors. Either way, customers are affected and orders are lost.
The core problem in one sentence:
The system was designed for a steady 150 orders per minute.
At 300 per minute it is being asked to do twice the work
it was ever built to handle, with no way to expand.

Q3 — Improvement Suggestion
Question: Suggest one concrete improvement that would allow the system
to handle higher load. Explain why it helps.
Improvement: Increase the number of parallel workers
This is the single most direct and effective fix for this specific problem.
The logic:
Current setup:   5 workers  ×  30 orders each  =  150 orders per minute
Doubled workers: 10 workers ×  30 orders each  =  300 orders per minute
By doubling the number of parallel workers from 5 to 10,
the system's capacity doubles exactly — from 150 to 300 orders per minute —
which perfectly matches the spike in demand described in Q2.

Adding more workers requires no changes to the existing code at all.
You simply run more instances of the same worker in parallel.
On cloud platforms like AWS or Google Cloud this can be done
automatically in seconds — the platform detects the spike and
spins up new workers instantly, then removes them when traffic drops.
This approach is called horizontal scaling — and it is the
industry standard solution for exactly this type of problem.
Verification:
If orders spike to 300 per minute:

  Before improvement:  5 workers  → capacity 150/min → 150 orders overflow → crash
  After improvement:  10 workers  → capacity 300/min → 0 orders overflow   → stable




