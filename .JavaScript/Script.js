// static/js/script.js
document.addEventListener('DOMContentLoaded', function () {
    let selectedSeat = null;
     const seatDivs = document.querySelectorAll('.seat.available');
    const seatInput = document.getElementById('seat-input');
    const form = document.getElementById('confirm-form');
    const selectedText = document.getElementById('selected-seat');

    seatDivs.forEach(seat => {
        seat.addEventListener('click', () => {
        const seatId = seat.dataset.seat;
        seatInput.value = seatId;
        selectedText.textContent = `선택한 좌석: ${seatId}`;
        form.submit();  // 바로 confirm으로 POST
    });
  });

    document.getElementById('confirm-form').addEventListener('submit', function (e) {
        if (!selectedSeat) {
            e.preventDefault();
            alert('좌석을 선택하세요.');
        }
    });
});

function confirmBooking() {
    return confirm("정말 예매하시겠습니까?");
}
