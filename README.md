# SAML Service

The SAML Service is designed to be used as an Authnetication Microwervice that is a configurable SAML Assertion toa given Identity Provider.

## Properties

| Name  | Type | Description |
| ------------- | ------------- | ------------- |
| Service Provider URL | text | Assertion Endpoint for the intended Identity Provider |
| Entity ID | text | URL to SAML Entitiy Identifier |
| Metadata | text | Raw XML defining the Identity Provider Metadata |
| Session Max Duration (Seconds) | numeric | The amount of time in seconds that a user can remain logged in to the Experience |
| Login Page Link | page-link | After successfully logging in, this setting will direct the user to the appropriate page. |
| Error Page Link | page-link | In case of an error during the login process, this setting will direct the user to the appropriate page. |
| Profile Service Uri | text | If a profile service is identified, it will be notified that a user logged in, and the email address will be set automatically
|

## Routes

** Note: All API Routes, excluding the Lumavate specific routes (discover, render, login, etc) are private and not intended to be called outside of the service. **
All routes are defined in app/routes/saml.py

