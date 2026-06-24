document.querySelectorAll(".alert").forEach((alert) => {
  setTimeout(() => {
    if (window.bootstrap) {
      const instance = bootstrap.Alert.getOrCreateInstance(alert);
      instance.close();
    }
  }, 4500);
});
