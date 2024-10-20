-- TPC TPC-H Parameter Substitution (Version 2.17.3 build 0)
-- using 1723123854 as a seed to the RNG


select
	ps_partkey,
	sum(ps_supplycost * ps_availqty) as "value"
from
	partsupp,
	supplier,
	nation
where
	ps_suppkey = s_suppkey
	and s_nationkey = n_nationkey
	and n_name = 'VIETNAM'
group by
	ps_partkey having
		sum(ps_supplycost * ps_availqty) > (
			select
				sum(ps_supplycost * ps_availqty) * 0.0000100000
			from
				partsupp,
				supplier,
				nation
			where
				ps_suppkey = s_suppkey
				and s_nationkey = n_nationkey
				and n_name = 'VIETNAM'
		)
order by
	"value" desc
limit 1;
