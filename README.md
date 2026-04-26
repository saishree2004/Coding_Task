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
