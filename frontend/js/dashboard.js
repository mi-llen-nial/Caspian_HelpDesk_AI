document.addEventListener("DOMContentLoaded", async () => {
  try {
    const data = await apiGet("/analytics/overview");
    document.getElementById("totalTickets").textContent = data.total_tickets;
    document.getElementById("newToday").textContent = data.new_today;
    document.getElementById("autoClosed").textContent = `${data.auto_closed_percent.toFixed(1)}%`;
    document.getElementById("classificationAccuracy").textContent =
      data.classification_accuracy != null ? `${data.classification_accuracy.toFixed(1)}%` : "—";
  } catch (err) {
    console.error(err);
  }
});

