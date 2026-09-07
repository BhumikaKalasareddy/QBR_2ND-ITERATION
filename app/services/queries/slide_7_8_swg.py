def get_slide_7_swg_kpi_query() -> str:
    """
    Returns SQL query for Slide 7 (SWG KPI / Overview).
    Fetches SWG architecture flags (Cloud/On-Prem/Hybrid), node counts, traffic volumes,
    and user adoption categories.
    """
    return """
    WITH pa_swg_base AS (
      SELECT
        sf_id,
        Account_Name,
        ConsolidatedprimaryExternalId,
        COALESCE(is_child_account, 'No') AS is_child_account,
        COALESCE(Account_ARR, 0) AS account_arr,
       
        -- Deployment & Architecture Flags
        COALESCE(SWG_On_Prem_Flag, 'FALSE') AS SWG_On_Prem_Flag,
        COALESCE(SWG_Cloud_Flag, 'FALSE') AS SWG_Cloud_Flag,
        COALESCE(swg_only_nodes, 0) AS swg_only_nodes,

        -- BPS SWG Telemetry Raw Metrics
        COALESCE(bps_telemetry_license_nodes_ag, 0) AS bps_telemetry_license_nodes_ag,
        COALESCE(bps_telemetry_count_user_ag, 0) AS bps_telemetry_count_user_ag,
        COALESCE(bps_telemetry_total_traffic_gb, 0.0) AS bps_telemetry_total_traffic_gb,
        COALESCE(bps_telemetry_user_adoption_cat, 'N/A') AS bps_telemetry_user_adoption_cat
      FROM `svc-edp-reporting-prod.edp_dp_telemetry.product_adoption_v1`
      WHERE is_child_account = 'No' -- Filters for Consolidated Parent summary rows
    )

    SELECT
      -- 1. Account Identity & Family Grouping
      Account_Name AS consolidated_account_name,
      COALESCE(NULLIF(TRIM(ConsolidatedprimaryExternalId), ''), sf_id) AS consolidated_account_id,
      sf_id AS child_sf_ids_aggregated,
      account_arr,

      -- 2. SWG Deployment & Architecture Footprint
      SWG_On_Prem_Flag,
      SWG_Cloud_Flag,
      swg_only_nodes,
      CASE
        WHEN SWG_Cloud_Flag = 'TRUE' AND SWG_On_Prem_Flag = 'TRUE' THEN 'Hybrid (Cloud + On-Prem)'
        WHEN SWG_Cloud_Flag = 'TRUE' THEN 'Cloud SWG Only'
        WHEN SWG_On_Prem_Flag = 'TRUE' THEN 'On-Prem SWG Only'
        ELSE 'None'
      END AS swg_deployment_footprint,

      -- 3. Telemetry Raw Numbers
      bps_telemetry_license_nodes_ag,
      bps_telemetry_count_user_ag,
      bps_telemetry_total_traffic_gb,

      -- 4. User Adoption Percentage & Category
      SAFE_DIVIDE(bps_telemetry_count_user_ag, NULLIF(bps_telemetry_license_nodes_ag, 0)) AS swg_user_adoption_pct,
      bps_telemetry_user_adoption_cat AS swg_user_adoption_category,

      -- 5. SWG Cloud Traffic Category (Exact Custom Logic)
      CASE
        WHEN (bps_telemetry_license_nodes_ag IS NULL OR bps_telemetry_license_nodes_ag = 0)
         AND (bps_telemetry_count_user_ag = 0 OR bps_telemetry_count_user_ag IS NULL) THEN 'N/A'
        WHEN (COALESCE(bps_telemetry_total_traffic_gb, 0) * 1.0) / NULLIF(bps_telemetry_license_nodes_ag, 0) <= 1 THEN 'Low'
        WHEN (COALESCE(bps_telemetry_total_traffic_gb, 0) * 1.0) / NULLIF(bps_telemetry_license_nodes_ag, 0) < 7 THEN 'Medium'
        ELSE 'High'
      END AS swg_cloud_traffic_category

    FROM pa_swg_base
    WHERE LOWER(Account_Name) LIKE LOWER(@account_name_param)

    -- De-duplication check ensuring 1 row per consolidated account
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY COALESCE(NULLIF(TRIM(ConsolidatedprimaryExternalId), ''), Account_Name)
      ORDER BY account_arr DESC
    ) = 1
    ORDER BY account_arr DESC;
    """


def get_slide_8_swg_tau_query() -> str:
    """
    Returns SQL query for Slide 8 (SWG TAU - Telemetry & Traffic Volumes).
    Queries bps_telemetry table for total users, requests, traffic volumes (GB/TB), and regional share %.
    """
    return """
    SELECT
      -- Account / Entity Identifiers
      COALESCE(NULLIF(TRIM(mdm_glbl_parent_name), ''), companyname) AS account_name,
      sf_integration_id AS child_sf_id,
      tenant_id,
      tenant_BPS_id,

      -- Regional / Geographic Identifiers (Region, Geo, City)
      location AS region,
      countrycode AS geo,
      city AS city_pop,

      -- Traffic Counts
      SUM(COALESCE(count_req, count_req_, 0)) AS total_requests,
      SUM(COALESCE(count_user, count_user_, 0)) AS total_users,

      -- Raw Download and Upload Volumes (Bytes to GB & TB)
      ROUND(SUM(COALESCE(download, download_, 0)) / 1e9, 2) AS download_gb,
      ROUND(SUM(COALESCE(upload, upload_, 0)) / 1e9, 2) AS upload_gb,
     
      -- Total SWG Traffic Volumes
      ROUND(SUM(COALESCE(download, download_, 0) + COALESCE(upload, upload_, 0)) / 1e9, 2) AS total_traffic_gb,
      ROUND(SUM(COALESCE(download, download_, 0) + COALESCE(upload, upload_, 0)) / 1e12, 3) AS total_traffic_tb,

      -- Regional Traffic Share Percentage per Account
      ROUND(
        SAFE_DIVIDE(
          SUM(COALESCE(download, download_, 0) + COALESCE(upload, upload_, 0)),
          SUM(SUM(COALESCE(download, download_, 0) + COALESCE(upload, upload_, 0))) OVER (PARTITION BY sf_integration_id)
        ) * 100,
        2
      ) AS region_traffic_share_pct

    FROM `svc-edp-reporting-prod.edp_dp_telemetry.bps_telemetry`
    WHERE product = 'SWG'
      AND LOWER(COALESCE(NULLIF(TRIM(mdm_glbl_parent_name), ''), companyname)) LIKE LOWER(@account_name_param)

    GROUP BY 1, 2, 3, 4, 5, 6, 7
    ORDER BY total_traffic_gb DESC;
    """