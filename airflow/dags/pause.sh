#!/bin/bash

# List of DAG IDs hardcoded from the provided file
dag_ids=("create_polls_dag" "create_polls_dag_frequent" "cast_votes_dag" "cast_votes_dag_weekend" "view_poll_result_dag" "view_poll_result_dag_weekend" "view_all_polls_dag" "view_all_polls_dag_weekend")

# Pause all DAGs
echo "Pausing all DAGs..."

for dag_id in "${dag_ids[@]}"; do
    echo "Pausing DAG: $dag_id"
    airflow dags pause "$dag_id"
done

echo "All DAGs have been paused."

