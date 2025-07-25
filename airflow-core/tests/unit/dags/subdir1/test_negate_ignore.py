#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

from datetime import datetime

from airflow.models.dag import DAG
from airflow.providers.standard.operators.bash import BashOperator

DEFAULT_DATE = datetime(2019, 12, 1)

dag = DAG(dag_id="test_dag_under_subdir1", start_date=DEFAULT_DATE, schedule=None)
task = BashOperator(task_id="task1", bash_command='echo "test dag under sub directory subdir2"', dag=dag)
