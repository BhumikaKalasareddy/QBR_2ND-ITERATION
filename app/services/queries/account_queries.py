def get_all_accounts_query() -> str:
    """SQL query to populate the dynamic customer selector in Streamlit UI."""
    return """
    SELECT DISTINCT TRIM(Account_Name) AS Account_Name 
    FROM `svc-edp-reporting-prod.edp_dp_telemetry.product_adoption_v1`
    WHERE Account_Name IS NOT NULL 
      AND TRIM(Account_Name) != ''
    ORDER BY Account_Name ASC;
    """


def get_all_quarters_query() -> str:
    """SQL query to populate the quarter selector in Streamlit UI."""
    return """
    SELECT DISTINCT Normalized_Qtr 
    FROM `svc-edp-reporting-prod.Finance_workspace.ARR_Final_Monthly`
    WHERE Normalized_Qtr IS NOT NULL
    ORDER BY Normalized_Qtr DESC;
    """


def get_customer_details_query() -> str:
    """
    Unified SQL query joining Product Adoption and ARR records for a selected account and quarter.
    """
    return """
    WITH monthly_arr AS (
      SELECT
        Salesforce_Account_ID AS sfdc_id,
        Active_Month,
        Normalized_Qtr,
        ARR_Actual,
        vertical,
        ROW_NUMBER() OVER (
          PARTITION BY Salesforce_Account_ID, Active_Month 
          ORDER BY COALESCE(
            SAFE.PARSE_DATE('%Y %m(%b)', Active_Month),
            SAFE.PARSE_DATE('%Y-%m-%d', Active_Month)
          ) DESC
        ) AS rn
      FROM `svc-edp-reporting-prod.Finance_workspace.ARR_Final_Monthly`
      WHERE Entity = 'SSE'
        AND Salesforce_Account_ID IS NOT NULL
        AND Normalized_Qtr = @quarter
    )
    SELECT
      p.sf_id,
      p.Tenant_Id,
      p.Account_Name,
      p.ConsolidatedprimaryExternalId,
      p.parent_name,
      p.geo,
      p.region,
      p.country,
      COALESCE(p.vertical, arr.vertical) AS vertical,
      p.csmassignedname AS csm_name,
      p.entitlement_gtm_rep AS gtm_rep,
      p.Account_ARR AS adoption_arr,
      arr.ARR_Actual AS monthly_arr_amount,
      arr.Active_Month AS arr_active_month,
      p.beginning_arr,
      p.ending_arr,
      p.expansion,
      p.contraction,
      p.churn,
      p.next_renewal_date,
      p.next_renewal_quarter,
      p.next_renewal_acv,
      p.renewal_risk_score,
      p.renewal_risk_comments,
      p.H2Health AS h2_health,
      p.ManagementHealthScore AS health_score,
      p.CepStage AS cep_stage,
      p.AccountHealthSummary AS health_summary,
      p.CustomerRedamberReason AS red_amber_reason,
      p.AccountHealthLastUpdatedDate AS health_updated_date,
      p.bps_telemetry_adoption_pct AS adoption_pct,
      p.bps_telemetry_total_traffic_gb AS traffic_gb,
      p.bps_telemetry_count_user_ag AS user_count,
      p.CASB_Active_user AS casb_active_users,
      p.SWG_Cloud_Flag AS swg_cloud_active,
      p.SWG_On_Prem_Flag AS swg_onprem_active,
      p.feature_adoption_casb_adopt_category AS casb_adoption_category,
      p.bps_telemetry_user_adoption_cat AS user_adoption_category
    FROM `svc-edp-reporting-prod.edp_dp_telemetry.product_adoption_v1` p
    LEFT JOIN monthly_arr arr
      ON p.sf_id = arr.sfdc_id AND arr.rn = 1
    WHERE LOWER(p.Account_Name) LIKE LOWER(CONCAT('%', @account_name, '%'))
    LIMIT 1;
    """