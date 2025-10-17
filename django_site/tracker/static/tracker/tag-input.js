(function () {
  "use strict";

  function normaliseToken(value) {
    return value.replace(/\s+/g, " ").trim();
  }

  function createPill(value) {
    const pill = document.createElement("span");
    pill.className = "tag-pill";
    pill.dataset.value = value;

    const text = document.createTextNode(value);
    pill.appendChild(text);

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "tag-pill__remove";
    remove.dataset.removeTag = "true";
    remove.setAttribute("aria-label", `Remove ${value}`);
    remove.textContent = "×";
    pill.appendChild(remove);

    return pill;
  }

  function initialise(container) {
    const input = container.querySelector("[data-tag-source]");
    const hidden = container.querySelector("[data-tag-value]");
    const tagList = container.querySelector("[data-tag-list]");

    if (!input || !hidden || !tagList) {
      return;
    }

    let values = [];

    function syncHidden() {
      hidden.value = values.join(", ");
    }

    function render() {
      tagList.innerHTML = "";
      values.forEach((value) => {
        tagList.appendChild(createPill(value));
      });
    }

    function setValues(nextValues) {
      const seen = new Set();
      values = [];
      nextValues.forEach((value) => {
        const normalised = normaliseToken(value);
        if (!normalised) {
          return;
        }
        const key = normalised.toLowerCase();
        if (seen.has(key)) {
          return;
        }
        seen.add(key);
        values.push(normalised);
      });
      render();
      syncHidden();
    }

    function addValue(raw) {
      const normalised = normaliseToken(raw);
      if (!normalised) {
        return;
      }
      if (values.some((value) => value.toLowerCase() === normalised.toLowerCase())) {
        return;
      }
      values.push(normalised);
      render();
      syncHidden();
    }

    function removeValue(targetValue) {
      const key = targetValue.toLowerCase();
      values = values.filter((value) => value.toLowerCase() !== key);
      render();
      syncHidden();
    }

    function commitInput() {
      const raw = input.value;
      if (!raw) {
        return;
      }
      addValue(raw);
      input.value = "";
    }

    container.addEventListener("click", (event) => {
      const button = event.target.closest("[data-remove-tag]");
      if (!button) {
        return;
      }
      const pill = button.closest("[data-value]");
      if (!pill) {
        return;
      }
      const value = pill.dataset.value;
      if (value) {
        removeValue(value);
      }
    });

    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === ",") {
        event.preventDefault();
        commitInput();
        return;
      }
      if (event.key === "Backspace" && !input.value && values.length) {
        const last = values[values.length - 1];
        removeValue(last);
        input.value = last;
      }
    });

    input.addEventListener("change", () => {
      commitInput();
    });

    const initial = hidden.value
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean);

    if (initial.length) {
      setValues(initial);
    } else {
      const fromMarkup = Array.from(tagList.querySelectorAll("[data-value]"))
        .map((element) => element.getAttribute("data-value") || "")
        .filter(Boolean);
      setValues(fromMarkup);
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    document
      .querySelectorAll("[data-tag-input]")
      .forEach((element) => initialise(element));
  });
})();
