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

from collections.abc import Sequence
from typing import TYPE_CHECKING

from airflow.exceptions import AirflowException
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.version_compat import BaseOperator

if TYPE_CHECKING:
    from airflow.utils.context import Context

# MAX XCOM Size is 48KB, check discussion: https://github.com/apache/airflow/pull/1618#discussion_r68249677
MAX_XCOM_SIZE = 49344


class GCSToLocalFilesystemOperator(BaseOperator):
    """
    Downloads a file from Google Cloud Storage.

    If a filename is supplied, it writes the file to the specified location, alternatively one can
    set the ``store_to_xcom_key`` parameter to True push the file content into xcom. When the file size
    exceeds the maximum size for xcom it is recommended to write to a file.

    .. seealso::
        For more information on how to use this operator, take a look at the guide:
        :ref:`howto/operator:GCSToLocalFilesystemOperator`

    :param bucket: The Google Cloud Storage bucket where the object is.
        Must not contain 'gs://' prefix. (templated)
    :param object_name: The name of the object to download in the Google cloud
        storage bucket. (templated)
    :param filename: The file path, including filename,  on the local file system (where the
        operator is being executed) that the file should be downloaded to. (templated)
        If no filename passed, the downloaded data will not be stored on the local file
        system.
    :param store_to_xcom_key: If this param is set, the operator will push
        the contents of the downloaded file to XCom with the key set in this
        parameter. If not set, the downloaded data will not be pushed to XCom. (templated)
    :param gcp_conn_id: (Optional) The connection ID used to connect to Google Cloud.
    :param impersonation_chain: Optional service account to impersonate using short-term
        credentials, or chained list of accounts required to get the access_token
        of the last account in the list, which will be impersonated in the request.
        If set as a string, the account must grant the originating account
        the Service Account Token Creator IAM role.
        If set as a sequence, the identities from the list must grant
        Service Account Token Creator IAM role to the directly preceding identity, with first
        account from the list granting this role to the originating account (templated).
    :param file_encoding: Optional encoding used to decode file_bytes into a serializable
        string that is suitable for storing to XCom. (templated).
    """

    template_fields: Sequence[str] = (
        "bucket",
        "object_name",
        "filename",
        "store_to_xcom_key",
        "impersonation_chain",
        "file_encoding",
    )
    ui_color = "#f0eee4"

    def __init__(
        self,
        *,
        bucket: str,
        object_name: str,
        filename: str | None = None,
        store_to_xcom_key: str | None = None,
        gcp_conn_id: str = "google_cloud_default",
        impersonation_chain: str | Sequence[str] | None = None,
        file_encoding: str = "utf-8",
        **kwargs,
    ) -> None:
        if filename is not None and store_to_xcom_key is not None:
            raise ValueError("Either filename or store_to_xcom_key can be set")
        super().__init__(**kwargs)
        self.bucket = bucket
        self.filename = filename
        self.object_name = object_name
        self.store_to_xcom_key = store_to_xcom_key
        self.gcp_conn_id = gcp_conn_id
        self.impersonation_chain = impersonation_chain
        self.file_encoding = file_encoding

    def execute(self, context: Context):
        self.log.info("Executing download: %s, %s, %s", self.bucket, self.object_name, self.filename)
        hook = GCSHook(
            gcp_conn_id=self.gcp_conn_id,
            impersonation_chain=self.impersonation_chain,
        )

        if self.store_to_xcom_key:
            file_size = hook.get_size(bucket_name=self.bucket, object_name=self.object_name)
            if file_size < MAX_XCOM_SIZE:
                file_bytes = hook.download(bucket_name=self.bucket, object_name=self.object_name)
                context["ti"].xcom_push(key=self.store_to_xcom_key, value=str(file_bytes, self.file_encoding))
            else:
                raise AirflowException("The size of the downloaded file is too large to push to XCom!")
        else:
            hook.download(bucket_name=self.bucket, object_name=self.object_name, filename=self.filename)

    def get_openlineage_facets_on_start(self):
        from airflow.providers.common.compat.openlineage.facet import Dataset
        from airflow.providers.openlineage.extractors import OperatorLineage

        return OperatorLineage(
            inputs=[Dataset(namespace=f"gs://{self.bucket}", name=self.object_name)],
            outputs=[Dataset(namespace="file", name=self.filename)] if self.filename else [],
        )
