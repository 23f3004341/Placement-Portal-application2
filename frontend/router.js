const publicPages = new Set(["home", "analytics", "login", "register"]);

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

function resolvePage(hash, user) {
  let page = hash.replace(/^#/, "") || (user ? "dashboard" : "home");

  if (!user && !publicPages.has(page)) return "login";
  if (user && ["login", "register"].includes(page)) return "dashboard";
  if (user && !protectedPages.has(page)) return "dashboard";
  return page;
}

window.resolvePage = resolvePage;
