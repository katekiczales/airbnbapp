# Summer Home Recommender

## System Design Diagram

## Explanation of Recommender Algorithm
- Listings comes from properties_service
- User attributes come from users_service
- Interactions come from /data/interactions.json
- Building user affinity (i.e., their preferences):
    - Search the interactions data to find all interactions for the current user. Collect the 
  features and tags for every property involved in these interactions.
    - Assign views (viewing a property on the explore page) a weight of 1 and saves (saving a property on the explore page)
  a weight of 3 (to reflect the interest users are likely showing through each action)
- Additional Scores
  - Affordability (afford_score): compares a property's nightly_price to the user’s budget. Gives 
  full credit (1.0) when the price is less than or equal to the budget, then reduces as the price rises above the budget.
  - Environment (env_score): gives 1.0 if the property’s tags contain the user’s preferred_env, else 0.0
  - Preferences (pref_score): gives the average of the user’s affinity values for any tokens (features/tags) on the 
  property that also appear in the users interaction history. Gives 0.0 if there is no overlap or the user has no interaction history.
  - These scores (afford_score, env_score, and pref_score) are combined into a single score and normalized.
  Affordability is given the greatest weight. Preferences are given a modest wait, especially since having few interactions 
  shouldn't greatly skew the results. This parameter could be tuned to be optimal for the user.
  - All properties are scores as a vector and the top N are selected and shown to the user. The percent match of the property
  is also shown.

## Explanation of LLM integration

- The logic for the LLM integration is owned by properties_service.py
- The API key is imported from config_private, which is not tracked by git to ensure privacy
- The service uses the DeepSeek LLM through OpenRouter's API
- It sends a pre-written prompt in the POST request's payload through an OpenRouter URL
- The prompt requests 25 properties, each with only the required fields 
(id, location, type, nightly_price, features, tags, capacity, lat, lon)
- The prompt asks the model to return only JSON
- The returned properties can be written directly to the disk (after doing some error handling in case the returned 
format is not what was expected or nothing was returned)
- The API-STYLE/public function first checks if the properties data already exists. If it does, it just returns it.
Otherwise, it means this is the first time the page has been visited, so the properties are generated.

## Works Cited