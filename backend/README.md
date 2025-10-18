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

---

## Response workflow overview

The platform supports two response flows: applicants applying to company vacancies and education organizations exchanging interest lists with companies. The sections below summarise available APIs, the roles that can call them, and how the status lifecycles behave.

### Vacancy applications (applicants ↔ companies)

Status lifecycle: `pending → approved|rejected` (company decision) or `pending → cancelled` (applicant rollback).【F:backend/database/schema/base.py†L154-L198】

#### Applicant actions

All applicant-facing routes are namespaced under `/v1/me/applicant`. Tokens must belong to a user with the `applicant` role.

| Purpose | Method & path | Notes |
| --- | --- | --- |
| List your applications | `GET /v1/me/applicant/vacancies/applications` | Optional query params: `limit`, `offset`, `status` to filter by `pending`, `approved`, `rejected`, or `cancelled`. Ordered by newest first.【F:backend/api/routers/applicants.py†L286-L315】|
| Apply to a vacancy | `POST /v1/me/applicant/vacancies/{vacancy_id}/applications` | Works only for published vacancies. Reuses an existing cancelled record by flipping it back to `pending`; otherwise returns 400 if an active application already exists.【F:backend/api/routers/applicants.py†L317-L352】|
| Cancel your application | `POST /v1/me/applicant/vacancies/{vacancy_id}/applications/cancel` | Only pending or approved requests you created can be cancelled. Reviewed (rejected) applications remain immutable.【F:backend/api/routers/applicants.py†L354-L387】|

The response payloads follow `ApplicantVacancyApplicationResponse` which embeds the vacancy snapshot so the UI can render cards without extra lookups.【F:backend/api/routers/applicants.py†L90-L102】

#### Company review

Company tokens operate on `/v1/me/company` routes. They can page through applications globally or per vacancy and change statuses while the application is `pending`.

| Purpose | Method & path | Notes |
| --- | --- | --- |
| List applications across all vacancies | `GET /v1/me/company/vacancies/applications` | Supports `limit`, `offset`, `status`, and `vacancy_id` filters. Use when showing an inbox view.【F:backend/api/routers/companies.py†L328-L372】|
| List applications for one vacancy | `GET /v1/me/company/vacancies/{vacancy_id}/applications` | Same filters minus `vacancy_id`. Validates that the vacancy belongs to the company before listing.【F:backend/api/routers/companies.py†L374-L406】|
| Approve an application | `POST /v1/me/company/vacancies/{vacancy_id}/applications/{application_id}/approve` | Allowed only while status is `pending`. Automatically enriches the payload with applicant profile and email for UI display.【F:backend/api/routers/companies.py†L408-L431】|
| Reject an application | `POST /v1/me/company/vacancies/{vacancy_id}/applications/{application_id}/reject` | Same guards as approval; returns 400 if the record is already cancelled/reviewed.【F:backend/api/routers/companies.py†L433-L456】|

### Internship engagements (education ↔ companies)

Education organisations publish internship lists that can be shared with companies. Either side can initiate an engagement, and both sides see the same status record. Status lifecycle mirrors vacancy applications: `pending → approved|rejected` (counterparty decision) or `pending → cancelled` (initiator rollback).【F:backend/database/schema/base.py†L333-L374】

#### Education-side flow

Education users work under `/v1/me/education/internships/{internship_id}`. Ensure the internship list belongs to the authenticated organisation and is `published` before initiating contact.

| Purpose | Method & path | Notes |
| --- | --- | --- |
| List engagements for an internship | `GET /v1/me/education/internships/{internship_id}/responses` | Paginates with `limit`, `offset`, and optional `status` filter. Only available to the internship owner.【F:backend/api/routers/education_internships.py†L595-L611】|
| Notify a company about an internship | `POST /v1/me/education/internships/{internship_id}/responses` | Creates (or reopens) an engagement targeting `company_id` while the internship is published. Reuses cancelled/rejected entries by resetting them to `pending`.【F:backend/api/routers/education_internships.py†L613-L662】|
| Cancel an education-initiated engagement | `POST /v1/me/education/internships/{internship_id}/responses/{engagement_id}/cancel` | Only for engagements the education side started. No-op if already cancelled.【F:backend/api/routers/education_internships.py†L664-L690】|
| Approve a company offer | `POST /v1/me/education/internships/{internship_id}/responses/{engagement_id}/approve` | Accepts company-initiated engagements in `pending` state.【F:backend/api/routers/education_internships.py†L693-L717】|
| Reject a company offer | `POST /v1/me/education/internships/{internship_id}/responses/{engagement_id}/reject` | Rejects company-initiated engagements in `pending` state.【F:backend/api/routers/education_internships.py†L720-L744】|

Responses include company contact information through `EducationInternshipEngagementResponse`, so frontend can render cards with profile and email links.【F:backend/api/routers/education_internships.py†L116-L134】

#### Company-side flow

Companies browse education-created internships through `/v1/company/internships` routes. These endpoints mirror the education experience so both sides see a consistent timeline.

| Purpose | Method & path | Notes |
| --- | --- | --- |
| List engagements initiated with your company | `GET /v1/company/internships/responses` | Global inbox with `limit`, `offset`, optional `status`, and `internship_id` filters.【F:backend/api/routers/education_internships.py†L922-L941】|
| List engagements for one internship | `GET /v1/company/internships/{internship_id}/responses` | Narrowed view for a specific internship.【F:backend/api/routers/education_internships.py†L943-L962】|
| Tell an education org you are interested | `POST /v1/company/internships/{internship_id}/responses` | Initiates or reopens an engagement while the internship is `published`. Returns the education profile plus internship snapshot for UI rendering.【F:backend/api/routers/education_internships.py†L964-L1027】|
| Cancel a company-initiated engagement | `POST /v1/company/internships/{internship_id}/responses/{engagement_id}/cancel` | Only allowed if your company initiated the record. Safe to call multiple times.【F:backend/api/routers/education_internships.py†L1034-L1064】|
| Approve an education request | `POST /v1/company/internships/{internship_id}/responses/{engagement_id}/approve` | Confirms a `pending` engagement started by the education organisation.【F:backend/api/routers/education_internships.py†L1067-L1093】|
| Reject an education request | `POST /v1/company/internships/{internship_id}/responses/{engagement_id}/reject` | Rejects a `pending` education-initiated engagement.【F:backend/api/routers/education_internships.py†L1098-L1124】|

Company-focused responses embed education contact details and the internship payload through `CompanyInternshipEngagementResponse`, enabling the frontend to render action panels without extra fetches.【F:backend/api/routers/education_internships.py†L136-L161】

### Demo data expectations

Demo seeding now provisions example applications and engagements so that the response lists return data immediately after `make demo` or `make db-reset`. Use them to validate UI states quickly without manual setup.【F:backend/database/demo_seed.py†L360-L458】
