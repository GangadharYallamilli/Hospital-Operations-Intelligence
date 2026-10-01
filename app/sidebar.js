document.addEventListener("DOMContentLoaded", async () => {
    const body = document.body;
    const toggle = document.getElementById("sidebarToggle");
    const storageKey = "medanexaSidebarCollapsed";
    const mobile = window.matchMedia("(max-width: 700px)");

    let collapsed = localStorage.getItem(storageKey) === "true";
    if (mobile.matches && localStorage.getItem(storageKey) === null) collapsed = true;
    const syncToggle = () => {
        body.classList.toggle("sidebar-collapsed", collapsed);
        if (toggle) {
            toggle.setAttribute("aria-expanded", String(!collapsed));
            toggle.setAttribute("aria-label", collapsed ? "Open navigation" : "Close navigation");
            toggle.title = collapsed ? "Open navigation" : "Close navigation";
        }
    };
    syncToggle();

    if (toggle) {
        toggle.addEventListener("click", () => {
            collapsed = !collapsed;
            localStorage.setItem(storageKey, String(collapsed));
            syncToggle();
        });
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && mobile.matches && !collapsed) {
                collapsed = true;
                localStorage.setItem(storageKey, "true");
                syncToggle();
            }
        });
    }

    const currentPage = location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll(".workspace-nav a, .navigation .nav-item").forEach((link) => {
        const target = new URL(link.href, location.origin).pathname.split("/").pop();
        link.classList.toggle("active", target === currentPage);
        if (target === currentPage) link.setAttribute("aria-current", "page");
        else link.removeAttribute("aria-current");
    });

    try {
        const response = await fetch("/auth/me", { credentials: "same-origin" });
        if (response.status === 401) {
            location.replace("/home.html");
            return;
        }
        if (!response.ok) throw new Error("Could not load account details.");
        const { user } = await response.json();
        if (!user) return;
        const name = user.admin_name || user.email || "Hospital Admin";
        const hospital = user.hospital_name || "Hospital Workspace";
        const nameTargets = document.querySelectorAll("#userName, #userNameSidebar");
        const hospitalTargets = document.querySelectorAll("#userHospital, #userHospitalSidebar");
        const avatars = document.querySelectorAll("#userAvatar, #userAvatarSidebar");
        nameTargets.forEach((target) => { target.textContent = name; });
        hospitalTargets.forEach((target) => { target.textContent = hospital; });
        avatars.forEach((target) => { target.textContent = name.trim().charAt(0).toUpperCase() || "A"; });
    } catch (error) {
        console.error("Workspace account could not be loaded.", error);
    }

    const logout = document.getElementById("logoutButton");
    if (logout) {
        logout.addEventListener("click", async () => {
            logout.disabled = true;
            try {
                await fetch("/auth/logout", { method: "POST", credentials: "same-origin" });
            } finally {
                sessionStorage.removeItem("medanexaAnalyticsData");
                location.replace("/home.html");
            }
        });
    }
});

