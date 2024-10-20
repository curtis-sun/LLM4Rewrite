-- TPC TPC-H Parameter Substitution (Version 2.17.3 build 0)
-- using 1723123853 as a seed to the RNG


select
	o_orderpriority,
	count(*) as order_count
from
	orders
where
	o_orderdate >= date '1997-04-01'
	and o_orderdate < date '1997-04-01' + interval '3' month
	and exists (
		select
			*
		from
			lineitem
		where
			l_orderkey = o_orderkey
			and l_commitdate < l_receiptdate
	)
group by
	o_orderpriority
order by
	o_orderpriority
limit 1;
