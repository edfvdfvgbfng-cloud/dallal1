/**
 * Hotel Booking JavaScript
 * Handles booking functionality and payment processing
 */

class HotelBookingSystem {
    constructor() {
        this.currentHotel = null;
        this.bookingData = {};
        this.init();
    }

    init() {
        this.setupDatePickers();
        this.setupGuestSelector();
        this.setupCarRentalToggle();
        this.setupPriceCalculation();
        this.setupFormSubmission();
        this.loadSimilarHotels();
    }

    setupDatePickers() {
        const checkIn = document.getElementById('checkIn');
        const checkOut = document.getElementById('checkOut');

        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        checkIn.min = today;
        checkOut.min = today;

        // Update checkout minimum when checkin changes
        checkIn.addEventListener('change', () => {
            checkOut.min = checkIn.value;
            if (checkOut.value && checkOut.value < checkIn.value) {
                checkOut.value = checkIn.value;
            }
            this.calculateTotalPrice();
        });

        checkOut.addEventListener('change', () => {
            this.calculateTotalPrice();
        });
    }

    setupGuestSelector() {
        const guests = document.getElementById('guests');
        const roomsCount = document.getElementById('roomsCount');

        guests.addEventListener('change', () => {
            this.calculateTotalPrice();
        });

        roomsCount.addEventListener('change', () => {
            this.calculateTotalPrice();
        });
    }

    setupCarRentalToggle() {
        const addCarRental = document.getElementById('addCarRental');
        const carRentalOptions = document.getElementById('carRentalOptions');

        if (addCarRental && carRentalOptions) {
            addCarRental.addEventListener('change', () => {
                carRentalOptions.style.display = addCarRental.checked ? 'block' : 'none';
                this.calculateTotalPrice();
            });
        }
    }

    setupPriceCalculation() {
        const roomType = document.getElementById('roomType');
        roomType.addEventListener('change', () => {
            this.calculateTotalPrice();
        });
    }

    calculateTotalPrice() {
        const checkIn = document.getElementById('checkIn');
        const checkOut = document.getElementById('checkOut');
        const guests = document.getElementById('guests');
        const roomsCount = document.getElementById('roomsCount');
        const roomType = document.getElementById('roomType');
        const addCarRental = document.getElementById('addCarRental');

        if (!checkIn.value || !checkOut.value) {
            return;
        }

        // Calculate nights
        const startDate = new Date(checkIn.value);
        const endDate = new Date(checkOut.value);
        const nights = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));

        if (nights <= 0) {
            this.showError('تاريخ الخروج يجب أن يكون بعد تاريخ الدخول');
            return;
        }

        // Update nights display
        const nightsInfo = document.getElementById('nightsInfo');
        if (nightsInfo) {
            nightsInfo.textContent = `عدد الليالي: ${nights}`;
        }

        // Get hotel price (should be passed from backend)
        const hotelPrice = this.getHotelPrice(roomType.value);
        const basePrice = hotelPrice * nights * parseInt(roomsCount.value);

        // Calculate taxes and fees
        const taxes = basePrice * 0.15; // 15% taxes
        const fees = basePrice * 0.05; // 5% fees

        // Calculate car rental cost if added
        let carRentalCost = 0;
        if (addCarRental && addCarRental.checked) {
            carRentalCost = this.calculateCarRentalCost(nights);
        }

        // Calculate total
        const total = basePrice + taxes + fees + carRentalCost;

        // Update display
        this.updatePriceDisplay({
            basePrice,
            taxes,
            fees,
            carRentalCost,
            total,
            nights
        });
    }

    getHotelPrice(roomType) {
        // In production, this would come from the hotel data
        const priceMap = {
            'standard': 50000,
            'deluxe': 75000,
            'suite': 150000,
            'presidential': 300000
        };
        return priceMap[roomType] || 50000;
    }

    calculateCarRentalCost(nights) {
        const carType = document.querySelector('select[name="car_type"]')?.value || 'economy';
        const dailyRates = {
            'economy': 25000,
            'compact': 35000,
            'midsize': 45000,
            'luxury': 100000,
            'suv': 75000
        };
        return dailyRates[carType] * nights;
    }

    updatePriceDisplay(prices) {
        document.getElementById('basePrice').textContent = this.formatPrice(prices.basePrice);
        document.getElementById('taxes').textContent = this.formatPrice(prices.taxes);
        document.getElementById('fees').textContent = this.formatPrice(prices.fees);
        document.getElementById('totalPrice').textContent = this.formatPrice(prices.total);

        // Add car rental cost if applicable
        if (prices.carRentalCost > 0) {
            const carRentalRow = document.createElement('div');
            carRentalRow.className = 'price-row';
            carRentalRow.innerHTML = `
                <span>تأجير السيارة</span>
                <span>${this.formatPrice(prices.carRentalCost)}</span>
            `;
            const totalRow = document.querySelector('.price-row.total');
            if (totalRow) {
                totalRow.parentNode.insertBefore(carRentalRow, totalRow);
            }
        }
    }

    formatPrice(price) {
        return new Intl.NumberFormat('ar-IQ').format(price) + ' د.ع';
    }

    setupFormSubmission() {
        const form = document.getElementById('bookingForm');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.processBooking();
        });
    }

    async processBooking() {
        const form = document.getElementById('bookingForm');
        const formData = new FormData(form);

        // Validate form
        if (!this.validateForm(form)) {
            return;
        }

        // Show loading state
        this.showLoading();

        try {
            const response = await fetch('/api/hotel-booking/', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess(data.booking_reference);
            } else {
                this.showError(data.error || 'حدث خطأ أثناء معالجة الحجز');
            }
        } catch (error) {
            console.error('Error processing booking:', error);
            this.showError('حدث خطأ أثناء معالجة الحجز');
        } finally {
            this.hideLoading();
        }
    }

    validateForm(form) {
        const checkIn = document.getElementById('checkIn');
        const checkOut = document.getElementById('checkOut');
        const guestName = document.querySelector('input[name="guest_name"]');
        const guestEmail = document.querySelector('input[name="guest_email"]');
        const guestPhone = document.querySelector('input[name="guest_phone"]');

        if (!checkIn.value || !checkOut.value) {
            this.showError('يرجى تحديد تواريخ الدخول والخروج');
            return false;
        }

        if (new Date(checkOut.value) <= new Date(checkIn.value)) {
            this.showError('تاريخ الخروج يجب أن يكون بعد تاريخ الدخول');
            return false;
        }

        if (!guestName.value.trim()) {
            this.showError('يرجى إدخال اسمك الكامل');
            return false;
        }

        if (!guestEmail.value.trim() || !this.isValidEmail(guestEmail.value)) {
            this.showError('يرجى إدخال بريد إلكتروني صحيح');
            return false;
        }

        if (!guestPhone.value.trim()) {
            this.showError('يرجى إدخال رقم هاتف');
            return false;
        }

        return true;
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    showLoading() {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = '<div class="loading-spinner"></div>';
        document.body.appendChild(overlay);
    }

    hideLoading() {
        const overlay = document.querySelector('.loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }

    showSuccess(bookingReference) {
        const bookingCard = document.querySelector('.booking-form-card');
        bookingCard.innerHTML = `
            <div class="booking-success">
                <div class="success-icon">✅</div>
                <h2>تم الحجز بنجاح!</h2>
                <p>رقم الحجز الخاص بك:</p>
                <div class="booking-reference">${bookingReference}</div>
                <p>تم إرسال تفاصيل الحجز إلى بريدك الإلكتروني</p>
                <button class="btn btn-primary" onclick="window.location.href='/dashboard/enhanced/'">
                    العودة للوحة التحكم
                </button>
            </div>
        `;
    }

    showError(message) {
        alert(message); // In production, use a better notification system
    }

    async loadSimilarHotels() {
        const container = document.querySelector('.similar-hotels-list');
        if (!container) return;

        try {
            // In production, this would call an API to get similar hotels
            // For now, we'll show placeholder data
            container.innerHTML = `
                <div class="similar-hotel-item">
                    <img src="/static/img/placeholder-hotel.svg" alt="فندق" class="similar-hotel-image">
                    <div class="similar-hotel-info">
                        <div class="similar-hotel-name">فندق بغداد الفاخر</div>
                        <div class="similar-hotel-price">75,000 د.ع/ليلة</div>
                        <div class="similar-hotel-rating">⭐⭐⭐⭐⭐</div>
                    </div>
                </div>
                <div class="similar-hotel-item">
                    <img src="/static/img/placeholder-hotel.svg" alt="فندق" class="similar-hotel-image">
                    <div class="similar-hotel-info">
                        <div class="similar-hotel-name">فندق البصرة الحديث</div>
                        <div class="similar-hotel-price">65,000 د.ع/ليلة</div>
                        <div class="similar-hotel-rating">⭐⭐⭐⭐</div>
                    </div>
                </div>
                <div class="similar-hotel-item">
                    <img src="/static/img/placeholder-hotel.svg" alt="فندق" class="similar-hotel-image">
                    <div class="similar-hotel-info">
                        <div class="similar-hotel-name">فندق أربيل الكلاسيكي</div>
                        <div class="similar-hotel-price">55,000 د.ع/ليلة</div>
                        <div class="similar-hotel-rating">⭐⭐⭐⭐</div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading similar hotels:', error);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.hotelBookingSystem = new HotelBookingSystem();
});