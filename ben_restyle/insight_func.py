# this script is for identifying insights (outliers in the database)
# under each criteria selected

# define a function for the insights
def get_insights(county, category, client):
    if (category is None) or (client is None) or (client is None):
        return "we only have insights when all three criteria are chosen for now"

    else:
        client_list = ["Monticello Asset Management, Inc.",
                       "Accolade Property Management, Inc."]
        county_list = ["Dallas", "Mclennan", "Denton", "Tarrant", "Collin",
                       "Travis", "Williamson", "Taylor", "Smith", "General legal advice", "Comal"]
        category_list = ["Non-payment eviction at JP", "Non-payment eviction appeal", "Non-payment  eviction at JP and appeal at County Court", "Small claims lawsuit by tenant & prohibited conduct eviction at JP", "Small claims lawsuit by tenant", "Non-payment eviction at JP and Bankruptcy",
                         "Prohibited conduct eviction at JP", "Prohibited conduct eviction at County Court", "Demand letter from tenant regarding lease violations", "Non-payment eviction appeal at JP", "Non-payment eviction appeal at County Court and Court of Appeals"]

        assert client in client_list, "Invalid client"
        assert county in county_list, "Invalid county"
        assert category in category_list, "Invalid category"

        insight = "Under current criteria, no specific outlier could be found"
        if client == 'Monticello Asset Management, Inc.':
            if county == "Dallas":
                if category == "Non-payment eviction at JP":
                    insight = "The outliers are matter_id 40716-0009 and 40716-0007"
                    # why are they worked by only associates, but other ones are have paralegals
                    # is there sth particular about woodland park
                elif category == "Non-payment eviction appeal":
                    insight = "The outliers are matter_id 40716-0015 and 40716-0016"
                    # 0013 another outlier and the place matter or not
                elif category == "Non-payment  eviction at JP and appeal at County Court":
                    insight = "There are too few cases to determine outliers"
            elif county == "Mclennan":
                insight = "There are too few cases to determine outliers"
        elif client == "Accolade Property Management, Inc.":
            if county == "Denton":
                if category == "Non-payment eviction appeal":
                    insight = "The only possible outlier is 40418-003, but arguable"
                    # 0012 outlier since big partner time
                elif category == "Small claims lawsuit by tenant & prohibited conduct eviction at JP":
                    insight = "There are too few cases to determine outliers"
                elif category == "Small claims lawsuit by tenant":
                    insight = "There are too few cases to determine outliers"
            elif county == "Tarrant":
                if category == "Non-payment eviction appeal":
                    insight = "The outliers are matter_id 40418-0038 and 40418-0037"
                elif category == "Small claims lawsuit by tenant" or category == "Non-payment eviction at JP and appeal at County Court"\
                        or category == "Non-payment eviction at JP and Bankruptcy" or category == "Prohibited conduct eviction at JP":
                    insight = "There are too few cases to determine outliers"
            elif county == "Collin":
                if category == "Non-payment eviction appeal":
                    insight = "The only possible outlier is matter_id 40418-0006"
                    # probably flatfeeable
                elif category == "Non-payment eviction appeal at JP" or category == "Prohibited conduct eviction at County Court" \
                        or category == "Demand letter from tenant regarding lease violations":
                    insight = "There are too few cases to determine outliers"
            elif county == "Travis":
                if category == "Non-payment eviction appeal":
                    insight = "The outlier is matter_id 40418-0008"
                    # partner time
                elif category == "Non-payment eviction appeal at County Court and Court of Appeals":
                    insight = "There are too few cases to determine outliers"
            elif county == "Williamson":
                if category == "Non-payment eviction appeal":
                    insight = "There are too few cases to determine outliers"
            elif county == "Dallas":
                if category == "Prohibited conduct eviction at JP" or category == "Non-payment eviction appeal":
                    insight = "There are too few cases to determine outliers"
            elif county in ("Taylor", "Smith", "General legal advice", "Comal"):
                insight = "There are too few cases to determine outliers"

                # denton tarrant for accolo non-payment eviction appeal seems faltfeeable potentiallhy
