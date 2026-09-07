/**
 * Guest Reviews Section - Interactive Components
 */

document.addEventListener("DOMContentLoaded", function() {
  const viewMoreBtn = document.getElementById("viewMoreReviewsBtn");
  const modal = document.getElementById("moreReviewsModal");
  const closeBtn = document.getElementById("closeReviewsModal");
  const allReviewsContainer = document.getElementById("allReviewsContainer");

  if (!viewMoreBtn || !modal) return;

  let reviewsLoaded = false;

  // Open modal with all reviews
  viewMoreBtn.addEventListener("click", function() {
    modal.classList.add("is-open");
    modal.style.display = "flex";
    if (!reviewsLoaded) {
      loadAllReviews();
      reviewsLoaded = true;
    }
  });

  // Close modal
  closeBtn?.addEventListener("click", function() {
    closeModal();
  });

  // Close modal when clicking outside
  modal.addEventListener("click", function(e) {
    if (e.target === modal) {
      closeModal();
    }
  });

  // Close modal on ESC key
  document.addEventListener("keydown", function(e) {
    if (e.key === "Escape" && modal?.classList.contains("is-open")) {
      closeModal();
    }
  });

  function closeModal() {
    modal.classList.remove("is-open");
    setTimeout(() => {
      modal.style.display = "none";
    }, 300);
  }

  /**
   * Load all reviews via AJAX
   */
  function loadAllReviews() {
    // Show loading spinner
    allReviewsContainer.innerHTML = '<div class="spinner">Loading reviews...</div>';

    // Fetch reviews from API
    fetch("/api/reviews/", {
      method: "GET",
      headers: {
        "Accept": "application/json",
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load reviews");
        }
        return response.json();
      })
      .then((data) => {
        if (data.success && data.reviews) {
          renderReviews(data.reviews);
        } else {
          throw new Error("Invalid response format");
        }
      })
      .catch((error) => {
        console.error("Error loading reviews:", error);
        allReviewsContainer.innerHTML =
          '<p style="text-align:center;color:#999;padding:2rem">Unable to load reviews. Please try again later.</p>';
      });
  }

  /**
   * Render reviews in the modal
   */
  function renderReviews(reviews) {
    if (!reviews || reviews.length === 0) {
      allReviewsContainer.innerHTML =
        '<p style="text-align:center;color:#999;padding:2rem">No reviews available yet.</p>';
      return;
    }

    const reviewsHTML = reviews
      .map(
        (review) => `
      <div class="review-card card p-6" style="margin-bottom:0">
        <div class="text-gold review-stars">${renderStars(review.rating)}</div>
        <p class="mt-4 text-sm leading-relaxed text-ink/75">&ldquo;${escapeHTML(
          review.review_text
        )}&rdquo;</p>
        <div class="mt-5 flex items-center justify-between">
          <div class="flex items-center gap-2">
            ${review.guest_photo ? `<img src="${review.guest_photo}" alt="${review.guest_name}" class="h-8 w-8 rounded-full object-cover">` : ""}
            <div>
              <p class="text-sm font-semibold text-forest">${escapeHTML(review.guest_name)}</p>
              <p class="text-xs text-ink/50">${getSourceLabel(review.source)}</p>
            </div>
          </div>
        </div>
      </div>
    `
      )
      .join("");

    allReviewsContainer.innerHTML = `<div class="all-reviews-list">${reviewsHTML}</div>`;
  }
});

/**
 * Star rating display helper
 */
function renderStars(rating) {
  let stars = "";
  for (let i = 1; i <= 5; i++) {
    stars += i <= rating ? "★" : "☆";
  }
  return stars;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHTML(text) {
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  };
  return text.replace(/[&<>"']/g, (char) => map[char]);
}

/**
 * Get source label from source code
 */
function getSourceLabel(source) {
  const labels = {
    google: "Google Reviews",
    airbnb: "Airbnb",
    booking_com: "Booking.com",
    direct: "Direct Guest",
    other: "Guest Review",
  };
  return labels[source] || "Guest Review";
}
