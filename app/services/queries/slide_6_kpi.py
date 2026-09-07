def get_slide_6_kpi_query() -> str:
    """
    Returns the SQL query for Slide 6 (Key Metrics).
    Aggregates financial KPIs, ARR, opportunity pipeline, and product footprint 
    for a consolidated account.
    """
    return """
    WITH snapshot_max_date AS (
      SELECT MAX(snapshot_date) AS max_snap_date
      FROM `svc-edp-reporting-prod.edp_dp_sales.opportunity`
    ),

    -- 1. Pre-aggregate Opportunity metrics by 15-char SFDC ID
    opp_child_agg AS (
      SELECT
        SUBSTR(TRIM(t1.account_id_18_char), 1, 15) AS sf_id_15,
        SUM(t1.ACV_Amount_USD) AS opportunity_value,
        SUM(t1.forecast_amount_acv_usd) AS opportunity_forecast_value
      FROM `svc-edp-reporting-prod.edp_dp_sales.opportunity` t1
      INNER JOIN snapshot_max_date
        ON FORMAT_TIMESTAMP('%F %T', t1.snapshot_date) = FORMAT_TIMESTAMP('%F %T', snapshot_max_date.max_snap_date)
      WHERE t1.business_unit_c = 'Skyhigh'
        AND t1.account_id_18_char IS NOT NULL
      GROUP BY 1
    ),

    -- 2. Unnest comma-separated sf_ids to perform explicit, deterministic joins
    pa_unnested AS (
      SELECT
        pa.*,
        TRIM(single_sf_id) AS individual_sf_id_15
      FROM `svc-edp-reporting-prod.edp_dp_telemetry.product_adoption_v1` pa,
      UNNEST(SPLIT(pa.sf_id, ',')) AS single_sf_id
      WHERE pa.is_child_account = 'No'
    ),

    -- 3. Join unnested child IDs to opportunity CTE cleanly
    pa_opp_joined AS (
      SELECT
        pu.ConsolidatedprimaryExternalId,
        pu.Account_Name,
        pu.sf_id,
        pu.Account_ARR,
        pu.next_renewal_acv,
        pu.CASB_Customer,
        pu.is_casb_shadow_it_customer,
        pu.SWG_Cloud_Flag,
        pu.SWG_On_Prem_Flag,
        SUM(COALESCE(opp.opportunity_value, 0)) AS total_opportunity_value,
        SUM(COALESCE(opp.opportunity_forecast_value, 0)) AS total_opportunity_forecast_value
      FROM pa_unnested pu
      LEFT JOIN opp_child_agg opp
        ON SUBSTR(TRIM(pu.individual_sf_id_15), 1, 15) = opp.sf_id_15
      GROUP BY
        1, 2, 3, 4, 5, 6, 7, 8, 9
    )

    SELECT
      -- 1. Account Hierarchy Identification
      pa.Account_Name AS consolidated_account_name,
      pa.ConsolidatedprimaryExternalId AS consolidated_account_id,
      pa.sf_id AS child_sf_ids_aggregated,

      -- 2. Pre-aggregated Financial KPIs
      pa.Account_ARR AS total_account_arr,
      pa.next_renewal_acv AS total_renewal_acv,

      -- 3. Clean Opportunity ACV Totals
      pa.total_opportunity_value,
      pa.total_opportunity_forecast_value,

      -- 4. Product Footprint Categorization
      CASE
        WHEN (pa.CASB_Customer = 'TRUE' OR pa.is_casb_shadow_it_customer = 'TRUE')
         AND (pa.SWG_Cloud_Flag = 'TRUE' OR pa.SWG_On_Prem_Flag = 'TRUE') THEN 'Both (CASB + SWG)'
        WHEN (pa.CASB_Customer = 'TRUE' OR pa.is_casb_shadow_it_customer = 'TRUE') THEN 'CASB Only'
        WHEN (pa.SWG_Cloud_Flag = 'TRUE' OR pa.SWG_On_Prem_Flag = 'TRUE') THEN 'SWG Only'
        ELSE 'None'
      END AS product_footprint

    FROM pa_opp_joined pa
    WHERE LOWER(pa.Account_Name) LIKE LOWER(@account_name_param)

    -- Deduplication check to ensure exactly 1 row per parent entity
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY COALESCE(NULLIF(TRIM(pa.ConsolidatedprimaryExternalId), ''), pa.Account_Name)
      ORDER BY pa.Account_ARR DESC
    ) = 1
    ORDER BY total_account_arr DESC;
    """