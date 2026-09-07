# =========================================================
# SLIDE 11: SUPPORT CASES OVERVIEW & HEALTH
# =========================================================

def get_slide11_global_created_cases_query() -> str:
    """Slide 11 Top Summary: Global cases created within target date window."""
    return """
    SELECT 
      DATE_TRUNC(DATE(open_dt), MONTH) AS month_start_date,
      COUNT(DISTINCT sr_num) AS number_of_cases_created
    FROM `svc-edp-reporting-prod.edp_dp_customer_success.cases`
    WHERE open_dt >= '2025-12-01'
      AND open_dt < '2026-07-01'
    GROUP BY 1
    ORDER BY month_start_date ASC;
    """


def get_slide11_account_licensed_metrics_query() -> str:
    """Slide 11 Chart 1: Dynamic Account Licensing and App Deployment summary."""
    return """
    SELECT
      Account_Name,
      bps_telemetry_license_nodes_ag AS swg_licensed_users,
      CASB_User_Licensed AS casb_licensed_users,
      CASB_Active_user AS casb_active_users,
      feature_adoption_active_saa_s_apps_deployed_count AS casb_active_apps_deployed,
      feature_adoption_active_saa_s_deployed_count_excl_ms AS casb_msft_apps_deployed
    FROM `svc-edp-reporting-prod.edp_dp_telemetry.product_adoption_v1`
    WHERE LOWER(Account_Name) LIKE LOWER(@account_name_param)
      AND is_child_account = 'No'
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY COALESCE(NULLIF(TRIM(ConsolidatedprimaryExternalId), ''), Account_Name)
      ORDER BY Account_ARR DESC
    ) = 1;
    """


def get_slide11_case_trend_query() -> str:
    """Slide 11 Chart 2: Monthly case trend filtered dynamically by SFDC IDs."""
    return """
    WITH target_ids AS (
      SELECT TRIM(sf_id) AS sf_id FROM UNNEST(SPLIT(@sf_ids_str, ',')) AS sf_id
    )
    SELECT
      DATE_TRUNC(DATE(open_dt), MONTH) AS month_start_date,
      COUNT(DISTINCT sr_num) AS case_count
    FROM `svc-edp-reporting-prod.edp_dp_customer_success.cases`
    WHERE open_dt >= '2025-12-01'
      AND open_dt < '2026-07-01'
      AND (
        wc_party_org_d_sf_integration_id IN (SELECT sf_id FROM target_ids)
        OR service_cloud_account_id IN (SELECT sf_id FROM target_ids)
        OR skyhigh_top_arr_sf_id IN (SELECT sf_id FROM target_ids)
      )
    GROUP BY 1
    ORDER BY 1 ASC;
    """


def get_slide11_resolution_type_query() -> str:
    """Slide 11 Chart 3: Case Resolution Breakdown dynamically filtered by SFDC IDs."""
    return """
    WITH target_ids AS (
      SELECT TRIM(sf_id) AS sf_id FROM UNNEST(SPLIT(@sf_ids_str, ',')) AS sf_id
    )
    SELECT
      COALESCE(sub_status_i, 'Uncategorized') AS resolution_type,
      COUNT(DISTINCT sr_num) AS case_count
    FROM `svc-edp-reporting-prod.edp_dp_customer_success.cases`
    WHERE open_dt >= '2025-12-01'
      AND open_dt < '2026-07-01'
      AND (
        wc_party_org_d_sf_integration_id IN (SELECT sf_id FROM target_ids)
        OR service_cloud_account_id IN (SELECT sf_id FROM target_ids)
        OR skyhigh_top_arr_sf_id IN (SELECT sf_id FROM target_ids)
      )
      AND LOWER(status_i) IN ('closed', 'resolved')
    GROUP BY 1
    ORDER BY case_count DESC;
    """


def get_slide11_cases_by_product_query() -> str:
    """Slide 11 Product Breakdown: Cases count grouped by Product Vertical."""
    return """
    WITH target_ids AS (
      SELECT TRIM(sf_id) AS sf_id FROM UNNEST(SPLIT(@sf_ids_str, ',')) AS sf_id
    )
    SELECT
      COALESCE(product_vertical, product_attribute_c, 'Unknown') AS product,
      COUNT(DISTINCT sr_num) AS case_count
    FROM `svc-edp-reporting-prod.edp_dp_customer_success.cases`
    WHERE open_dt >= '2025-12-01'
      AND open_dt < '2026-07-01'
      AND (
        wc_party_org_d_sf_integration_id IN (SELECT sf_id FROM target_ids)
        OR service_cloud_account_id IN (SELECT sf_id FROM target_ids)
        OR skyhigh_top_arr_sf_id IN (SELECT sf_id FROM target_ids)
      )
    GROUP BY 1
    ORDER BY case_count DESC;
    """


def get_slide11_case_status_summary_query() -> str:
    """Slide 11 Chart 4: Case Status Breakdown dynamically filtered by SFDC IDs."""
    return """
    WITH target_ids AS (
      SELECT TRIM(sf_id) AS sf_id FROM UNNEST(SPLIT(@sf_ids_str, ',')) AS sf_id
    )
    SELECT
      COALESCE(status_i, 'Unknown') AS case_status,
      COUNT(DISTINCT sr_num) AS case_count
    FROM `svc-edp-reporting-prod.edp_dp_customer_success.cases`
    WHERE open_dt >= '2025-12-01'
      AND open_dt < '2026-07-01'
      AND (
        wc_party_org_d_sf_integration_id IN (SELECT sf_id FROM target_ids)
        OR service_cloud_account_id IN (SELECT sf_id FROM target_ids)
        OR skyhigh_top_arr_sf_id IN (SELECT sf_id FROM target_ids)
      )
    GROUP BY 1
    ORDER BY case_count DESC;
    """


# =========================================================
# SLIDE 12: CASE TRENDS & SEVERITY BREAKDOWN
# =========================================================

def get_slide12_entered_vs_closed_art_query() -> str:
    """
    Slide 12: Monthly Total Entered vs Total Closed cases & Average Resolution Time (ART in Days).
    Dynamic SFDC IDs via UNNEST(SPLIT(@sf_ids_str, ',')).
    """
    return """
    WITH target_sfdc_ids AS (
      SELECT TRIM(sfdc_id) AS sfdc_id
      FROM UNNEST(SPLIT(@sf_ids_str, ',')) AS sfdc_id
    ),
    base_cases AS (
      SELECT
        sr_num,
        open_dt,
        close_dt,
        COALESCE(
          NULLIF(SAFE_CAST(Total_ART AS FLOAT64), 0),
          NULLIF(SAFE_CAST(TOTAL_SR_DURATION AS FLOAT64), 0),
          NULLIF(SAFE_CAST(Net_SR_Duration AS FLOAT64), 0),
          TIMESTAMP_DIFF(close_dt, open_dt, DAY)
        ) AS calculated_art_days
      FROM `svc-edp-reporting-prod.edp_dp_customer_success.cases`
      WHERE (
        service_cloud_account_id IN (SELECT sfdc_id FROM target_sfdc_ids)
        OR skyhigh_top_arr_sf_id IN (SELECT sfdc_id FROM target_sfdc_ids)
        OR wc_party_org_d_sf_integration_id IN (SELECT sfdc_id FROM target_sfdc_ids)
      )
    ),
    entered_cases AS (
      SELECT
        FORMAT_DATE('%b-%y', DATE(open_dt)) AS Month,
        DATE_TRUNC(DATE(open_dt), MONTH) AS month_start,
        COUNT(DISTINCT sr_num) AS Total_Entered
      FROM base_cases
      WHERE open_dt IS NOT NULL
        AND DATE(open_dt) >= '2026-04-01'
        AND DATE(open_dt) < '2026-07-01'
      GROUP BY 1, 2
    ),
    closed_cases AS (
      SELECT
        FORMAT_DATE('%b-%y', DATE(close_dt)) AS Month,
        DATE_TRUNC(DATE(close_dt), MONTH) AS month_start,
        COUNT(DISTINCT sr_num) AS Total_Closed,
        ROUND(AVG(calculated_art_days), 1) AS ART_Days
      FROM base_cases
      WHERE close_dt IS NOT NULL
        AND DATE(close_dt) >= '2026-04-01'
        AND DATE(close_dt) < '2026-07-01'
      GROUP BY 1, 2
    )
    SELECT
      COALESCE(e.Month, c.Month) AS Month,
      COALESCE(e.Total_Entered, 0) AS Total_Entered,
      COALESCE(c.Total_Closed, 0) AS Total_Closed,
      COALESCE(c.ART_Days, 0.0) AS ART
    FROM entered_cases e
    FULL OUTER JOIN closed_cases c ON e.month_start = c.month_start
    ORDER BY COALESCE(e.month_start, c.month_start) ASC;
    """


def get_slide12_severity_breakdown_query() -> str:
    """
    Slide 12 Chart 3: Monthly Case breakdown by Initial Severity (Sev 1, Sev 2, Sev 3, Sev 4).
    Dynamic SFDC IDs via UNNEST(SPLIT(@sf_ids_str, ',')).
    """
    return """
    WITH target_sfdc_ids AS (
      SELECT TRIM(sfdc_id) AS sfdc_id
      FROM UNNEST(SPLIT(@sf_ids_str, ',')) AS sfdc_id
    )
    SELECT
      FORMAT_DATE('%b %Y', DATE(open_dt)) AS Month_Year,
      DATE_TRUNC(DATE(open_dt), MONTH) AS month_start,
      COUNT(DISTINCT IF(CAST(initial_severity AS STRING) LIKE '1%' OR CAST(sev_cd_i AS STRING) = '1', sr_num, NULL)) AS Severity_1,
      COUNT(DISTINCT IF(CAST(initial_severity AS STRING) LIKE '2%' OR CAST(sev_cd_i AS STRING) = '2', sr_num, NULL)) AS Severity_2,
      COUNT(DISTINCT IF(CAST(initial_severity AS STRING) LIKE '3%' OR CAST(sev_cd_i AS STRING) = '3', sr_num, NULL)) AS Severity_3,
      COUNT(DISTINCT IF(CAST(initial_severity AS STRING) LIKE '4%' OR CAST(sev_cd_i AS STRING) = '4', sr_num, NULL)) AS Severity_4
    FROM `svc-edp-reporting-prod.edp_dp_customer_success.cases`
    WHERE (
      CAST(service_cloud_account_id AS STRING) IN (SELECT sfdc_id FROM target_sfdc_ids)
      OR CAST(skyhigh_top_arr_sf_id AS STRING) IN (SELECT sfdc_id FROM target_sfdc_ids)
      OR CAST(wc_party_org_d_sf_integration_id AS STRING) IN (SELECT sfdc_id FROM target_sfdc_ids)
    )
    AND DATE(open_dt) >= '2026-03-01'
    AND DATE(open_dt) < '2026-07-01'
    GROUP BY 1, 2
    ORDER BY month_start ASC;
    """