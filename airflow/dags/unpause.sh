#!/bin/bash

# List of DAG IDs hardcoded from the provided file
dag_ids=("create_polls_dag" "create_polls_dag_frequent" "cast_votes_dag" "cast_votes_dag_weekend" "view_poll_result_dag" "view_poll_result_dag_weekend" "view_all_polls_dag" "view_all_polls_dag_weekend")

# Unpause all DAGs
echo "Unpausing all DAGs..."

for dag_id in "${dag_ids[@]}"; do
    echo "Unpausing DAG: $dag_id"
    airflow dags unpause "$dag_id"
done

echo "All DAGs have been unpaused."

