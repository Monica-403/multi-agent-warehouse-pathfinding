(() => {
    const storageKey = "warehouse-theme";
    const savedTheme = window.localStorage.getItem(storageKey);

    if (savedTheme === "light") {
        document.documentElement.dataset.theme = "light";
    }

    function updateToggle(theme) {
        document.querySelectorAll(".theme-toggle").forEach((button) => {
            const lightTheme = theme === "light";
            button.textContent = lightTheme ? "🌙 Dark" : "☀ Light";
            button.setAttribute(
                "aria-label",
                `Switch to ${lightTheme ? "dark" : "light"} theme`
            );
            button.setAttribute("aria-pressed", String(lightTheme));
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        updateToggle(document.documentElement.dataset.theme || "dark");

        document.querySelectorAll(".theme-toggle").forEach((button) => {
            button.addEventListener("click", () => {
                const theme =
                    document.documentElement.dataset.theme === "light"
                        ? "dark"
                        : "light";

                if (theme === "light") {
                    document.documentElement.dataset.theme = theme;
                } else {
                    delete document.documentElement.dataset.theme;
                }

                window.localStorage.setItem(storageKey, theme);
                updateToggle(theme);
            });
        });
    });
})();
