# ZOO-106 The visitor guide is slow and shows animals twice

**Reporter:** Mobile app team
**Pattern:** Database performance

> Scrolling the cat list on the app is slow, gets slower page after page, and when new
> cats arrive during a visit some cats appear twice while others are skipped. The DBA also
> says the service opens a new database connection for almost every query.

## Acceptance criteria

- `GET /v1/animals` pages with an opaque `cursor`: each response carries `next_cursor` (null on the last page) and the client passes it back to get the next page. Order stays newest arrival first, then highest id.
- Animals inserted between two page loads never shift the next page: no duplicates, no gaps.
- Serving a page costs **at most 2 SQL queries**, enclosure names included.
- The catalog query is served by an index: its `EXPLAIN QUERY PLAN` shows no table `SCAN` and no `TEMP B-TREE` sort.
- The whole process opens **at most 4 database connections**, however many requests run at once.

## Notes

Schema changes go through new migrations in `zoo_platform/migrations`. Never edit `0001_initial.sql`: it already ran in production.

## Done when

`python -m zoo test --mode hard 6` is green and the unit tests still pass.

## Read before you start

- [Use The Index, Luke: no offset](https://use-the-index-luke.com/no-offset)
- [SQLite EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)
