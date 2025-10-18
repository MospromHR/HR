## Postman setup

1. Create a new environment with a `baseUrl` variable that points to your running API instance (for example, `http://localhost:8000`).
2. Add a collection with the requests you need. For authenticated calls, create a `POST {{baseUrl}}/v1/auth/token` request that uses the *x-www-form-urlencoded* body with the fields:
   * `username` – the user's email address
   * `password` – the plain-text password
   * `grant_type` – set to `password`
3. Save the `access_token` and `refresh_token` from the response into collection variables (for example `accessToken`/`refreshToken`).
4. Configure the collection's Authorization tab to use the *Bearer Token* type and reference the `{{accessToken}}` variable so that every request reuses the latest token value.
5. When the access token expires, send a `POST {{baseUrl}}/v1/auth/token/refresh` request with a JSON body `{ "refresh_token": "{{refreshToken}}" }` and update the stored variables with the new values.

This setup lets you authenticate once per session and reuse the bearer token automatically across Postman requests.
