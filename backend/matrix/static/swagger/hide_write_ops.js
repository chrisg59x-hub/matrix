// C:\dev\matrix\matrix\static\swagger\hide_write_ops.js

(function () {
  /**
   * Utility: Fetch current user's role from the API
   * and store it in localStorage for later checks.
   */
  function fetchUserRole() {
    return fetch("/api/me/whoami/")
      .then(r => r.ok ? r.json() : Promise.resolve({}))
      .then(data => {
        if (data.biz_role) {
          localStorage.setItem("swagger_user_role", data.biz_role);
          localStorage.setItem("swagger_username", data.username || "");
        }
      })
      .catch(() => {
        // fallback to whatever was stored
      });
  }

  /**
   * Utility: Create or update the banner at top of Swagger UI
   */
  function showRoleBanner() {
    const role = localStorage.getItem("swagger_user_role") || "unknown";
    const user = localStorage.getItem("swagger_username") || "";
    const existing = document.getElementById("role-banner");
    const message = user
      ? `You are logged in as: ${user} (${role})`
      : `You are logged in as: ${role}`;
    const color = (role === "manager" || role === "admin") ? "#006400" : "#8B0000"; // green/red

    if (existing) {
      existing.textContent = message;
      existing.style.backgroundColor = color;
      return;
    }

    const div = document.createElement("div");
    div.id = "role-banner";
    div.textContent = message;
    div.style.cssText = `
      background-color: ${color};
      color: white;
      font-family: system-ui, sans-serif;
      font-size: 14px;
      font-weight: bold;
      text-align: center;
      padding: 8px 0;
      position: sticky;
      top: 0;
      z-index: 9999;
      box-shadow: 0
