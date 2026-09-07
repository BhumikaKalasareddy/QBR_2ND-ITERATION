def get_slide_7_casb_overview_query() -> str:
    """
    Returns the SQL query for Slide 7 (CASB Overview).
    Fetches CASB active users, licensing totals, SaaS app counts, and adoption categories.
    """
    return """
    WITH pa_base AS (
      SELECT
        sf_id,
        Account_Name,
        ConsolidatedprimaryExternalId,
        COALESCE(is_child_account, 'No') AS is_child_account,
        COALESCE(Account_ARR, 0) AS account_arr,
       
        -- Raw CASB User & License Counts
        COALESCE(CASB_Active_user, 0) AS CASB_Active_user,
        COALESCE(CASB_User_Licensed, 0) AS CASB_User_Licensed,
       
        -- Raw SaaS App Metrics
        COALESCE(feature_adoption_active_saa_s_deployed_count_excl_ms, 0) AS feature_adoption_active_saa_s_deployed_count_excl_ms,
        COALESCE(feature_adoption_active_saa_s_apps_deployed_count, 0) AS feature_adoption_active_saa_s_apps_deployed_count,
        COALESCE(feature_adoption_saa_s_apps_licensed_count, 0) AS feature_adoption_saa_s_apps_licensed_count
      FROM `svc-edp-reporting-prod.edp_dp_telemetry.product_adoption_v1`
      WHERE is_child_account = 'No' -- Filters for Consolidated Parent summary rows
    )

    SELECT
      -- Account Identifiers
      Account_Name AS consolidated_account_name,
      COALESCE(NULLIF(TRIM(ConsolidatedprimaryExternalId), ''), sf_id) AS consolidated_account_id,
      sf_id AS child_sf_ids_aggregated,
      account_arr,

      -- 1. Actual Numbers (Raw Aggregates)
      CASB_Active_user,
      CASB_User_Licensed,
      feature_adoption_active_saa_s_deployed_count_excl_ms,
      feature_adoption_active_saa_s_apps_deployed_count,
      feature_adoption_saa_s_apps_licensed_count,

      -- 2. CASB User Adoption % (Active / Licensed)
      SAFE_DIVIDE(CASB_Active_user, CASB_User_Licensed) AS casb_user_adoption_pct,

      -- 3. CASB User Adoption Category (Based on User Pct)
      CASE
        WHEN CASB_User_Licensed = 0 OR CASB_User_Licensed IS NULL THEN 'N/A'
        WHEN SAFE_DIVIDE(CASB_Active_user, CASB_User_Licensed) >= 0.70 THEN 'High'
        WHEN SAFE_DIVIDE(CASB_Active_user, CASB_User_Licensed) >= 0.30 THEN 'Medium'
        ELSE 'Low'
      END AS casb_user_adoption_category,

      -- 4. CASB Adoption Category (Based on SaaS apps excluding MS)
      CASE
        WHEN (CASB_Active_user = 0 OR CASB_Active_user IS NULL)
         AND (CASB_User_Licensed = 0 OR CASB_User_Licensed IS NULL) THEN 'N/A'  
        WHEN feature_adoption_active_saa_s_deployed_count_excl_ms >= 3 THEN 'High'  
        WHEN feature_adoption_active_saa_s_deployed_count_excl_ms >= 2 THEN 'Medium'
        ELSE 'Low'  
      END AS casb_adoption_category

    FROM pa_base
    WHERE LOWER(Account_Name) LIKE LOWER(@account_name_param)

    -- De-duplication check to ensure 1 clean record per consolidated account
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY COALESCE(NULLIF(TRIM(ConsolidatedprimaryExternalId), ''), Account_Name)
      ORDER BY account_arr DESC
    ) = 1
    ORDER BY account_arr DESC;
    """


def get_slide_8_casb_feature_adoption_query() -> str:
    """
    Returns the SQL query for Slide 8 (CASB Feature Adoption).
    Joins product adoption telemetry with casb.feature_adoption for tenant-level SaaS, IaaS, and Shadow IT details.
    """
    return """
    WITH latest_casb_feature_adoption AS (
      SELECT
        fa.Tenant_Id,
        fa.Tenant_BPS_Id,
        fa.Tenant_Name,
        fa.UCN,
        fa.Environment,
       
        -- SaaS App Licensing & Deployment
        fa.SaaS_Apps_Licensed_Count,
        fa.SaaS_Apps_Licensed_List,
        fa.All_SaaS_Apps_Deployed_Count,
        fa.All_SaaS_Apps_Deployed_List,
        fa.Active_SaaS_Apps_Deployed_Count,
        fa.Active_SaaS_Apps_Deployed_List,
        fa.Aggregated_SaaS_Score,
        fa.SaaS_App_Scores,
       
        -- IaaS App Licensing & Deployment
        fa.IaaS_Apps_Licensed_Count,
        fa.IaaS_Apps_Licensed_List,
        fa.All_IaaS_Apps_Deployed_Count,
        fa.All_IaaS_Apps_Deployed_List,
        fa.Active_IaaS_Apps_Deployed_Count,
        fa.Active_IaaS_Apps_Deployed_List,
        fa.Aggregated_IaaS_Score,
        fa.IaaS_App_Scores,
       
        -- Shadow IT & Reverse Proxy Deployment
        fa.Shadow_License_Purchased,
        fa.Aggregated_Shadow_Score,
        fa.All_Reverse_Proxy_Deployed_Apps,
        fa.Active_Reverse_Proxy_Deployed_Apps,
        fa._Digest_Date
      FROM `svc-edp-conformed-prod.casb.feature_adoption` fa
      WHERE fa._Digest_Date = DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
    )

    SELECT
      -- Account Identity & Family Hierarchy
      pa.Account_Name AS consolidated_account_name,
      COALESCE(NULLIF(TRIM(pa.ConsolidatedprimaryExternalId), ''), pa.sf_id) AS consolidated_account_id,
      pa.sf_id AS child_sf_id,

      -- CASB Slide 2 Tenant & Feature Adoption Fields
      fa.Tenant_Id,
      fa.Tenant_BPS_Id,
      fa.Tenant_Name,
      fa.UCN,
      fa.Environment,
     
      -- SaaS Breakdown
      COALESCE(fa.SaaS_Apps_Licensed_Count, 0) AS SaaS_Apps_Licensed_Count,
      COALESCE(fa.SaaS_Apps_Licensed_List, '') AS SaaS_Apps_Licensed_List,
      COALESCE(fa.All_SaaS_Apps_Deployed_Count, 0) AS All_SaaS_Apps_Deployed_Count,
      COALESCE(fa.All_SaaS_Apps_Deployed_List, '') AS All_SaaS_Apps_Deployed_List,
      COALESCE(fa.Active_SaaS_Apps_Deployed_Count, 0) AS Active_SaaS_Apps_Deployed_Count,
      COALESCE(fa.Active_SaaS_Apps_Deployed_List, '') AS Active_SaaS_Apps_Deployed_List,
      COALESCE(fa.Aggregated_SaaS_Score, 0.0) AS Aggregated_SaaS_Score,
      COALESCE(fa.SaaS_App_Scores, '[]') AS SaaS_App_Scores,
     
      -- IaaS Breakdown
      COALESCE(fa.IaaS_Apps_Licensed_Count, 0) AS IaaS_Apps_Licensed_Count,
      COALESCE(fa.IaaS_Apps_Licensed_List, '') AS IaaS_Apps_Licensed_List,
      COALESCE(fa.All_IaaS_Apps_Deployed_Count, 0) AS All_IaaS_Apps_Deployed_Count,
      COALESCE(fa.All_IaaS_Apps_Deployed_List, '') AS All_IaaS_Apps_Deployed_List,
      COALESCE(fa.Active_IaaS_Apps_Deployed_Count, 0) AS Active_IaaS_Apps_Deployed_Count,
      COALESCE(fa.Active_IaaS_Apps_Deployed_List, '') AS Active_IaaS_Apps_Deployed_List,
      COALESCE(fa.Aggregated_IaaS_Score, 0.0) AS Aggregated_IaaS_Score,
      COALESCE(fa.IaaS_App_Scores, '[]') AS IaaS_App_Scores,
     
      -- Shadow IT & Reverse Proxy
      COALESCE(fa.Shadow_License_Purchased, false) AS Shadow_License_Purchased,
      COALESCE(fa.Aggregated_Shadow_Score, 0.0) AS Aggregated_Shadow_Score,
      COALESCE(fa.All_Reverse_Proxy_Deployed_Apps, '') AS All_Reverse_Proxy_Deployed_Apps,
      COALESCE(fa.Active_Reverse_Proxy_Deployed_Apps, '') AS Active_Reverse_Proxy_Deployed_Apps,
      fa._Digest_Date

    FROM `svc-edp-reporting-prod.edp_dp_telemetry.product_adoption_v1` pa
    LEFT JOIN latest_casb_feature_adoption fa
      ON TRIM(CAST(pa.tenant_id AS STRING)) = TRIM(CAST(fa.Tenant_Id AS STRING))
      OR TRIM(CAST(pa.bps_telemetry_tenant_bps_id AS STRING)) = TRIM(CAST(fa.Tenant_BPS_Id AS STRING))
    WHERE pa.is_child_account = 'No' -- Consolidated Parent Summary Level
      AND LOWER(pa.Account_Name) LIKE LOWER(@account_name_param)
    ORDER BY pa.Account_ARR DESC;
    """