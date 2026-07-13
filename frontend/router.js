// Pages any visitor can open without being logged in.
const publicPages = new Set(["home", "analytics", "login", "register"]);

// Pages that require an authenticated session.
const protectedPages = new Set([
  "dashboard",
  "admin-companies",
  "admin-students",
  "admin-drives",
  "admin-applications",
  "company-drives",
  "company-applications",
  "student-drives",
  "student-applications",
  "profile",
]);

// Decide which page to actually show for a given hash and current user.
function resolvePage(hash, user) {
  let page = hash.replace(/^#/, "") || (user ? "dashboard" : "home");

  if (!user && !publicPages.has(page)) return "login";        // guest hitting a protected page
  if (user && ["login", "register"].includes(page)) return "dashboard"; // already logged in
  if (user && !protectedPages.has(page)) return "dashboard";  // unknown page -> safe default
  return page;
}

window.resolvePage = resolvePage;
