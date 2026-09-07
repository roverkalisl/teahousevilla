# Guest Reviews Feature - Setup & Configuration Guide

## Overview

The Guest Reviews feature allows you to display selected guest reviews directly on the Tea House Villa website without requiring visitors to leave the site. The feature includes:

- **Frontend Display**: Beautiful review cards showing guest ratings and testimonials
- **Admin Dashboard**: Complete review management interface
- **Google Integration Ready**: Support for official Google Business Profile API
- **Responsive Design**: Mobile-friendly carousel/stacked layout
- **Review Management**: Add, edit, delete, and control review visibility

## Features

### Frontend (Website Visitor View)

1. **Review Score Card** - Displays average rating, star count, and total review count
2. **Featured Reviews** - Shows 3 highlighted reviews in a grid layout
3. **View More Reviews Button** - Opens a modal to view all reviews without leaving the site
4. **Star Ratings** - Visual star ratings (★) for each review
5. **Guest Information** - Guest name, review source badge, and optional guest photo
6. **Responsive Layout** - Desktop grid and mobile-optimized display

### Admin Dashboard (Owner Control)

1. **Reviews List** - View all reviews with filtering options
2. **Search & Filter** - Filter by source (Google, Airbnb, etc.), rating (1-5 stars), status (Active/Inactive)
3. **Add Review** - Manually add reviews from real guests
4. **Edit Review** - Update review text, rating, guest name, and other details
5. **Delete Review** - Remove reviews from display
6. **Toggle Status** - Quickly activate/deactivate reviews without deleting
7. **Display Order** - Control the order reviews appear on the website
8. **Guest Photo** - Optional photo upload for reviews

## Installation & Setup

### 1. Database Setup

The feature uses the existing `Testimonial` model. No database migrations are required as the model already exists. If you haven't yet, create a superuser account:

```bash
python manage.py createsuperuser
```

### 2. Admin Access

Access the admin dashboard at:
```
https://yourdomain.com/admin-dashboard/
```

Or the public booking/admin area:
```
https://yourdomain.com/bookings/admin-login/
```

### 3. Add Your First Review

1. Go to **Admin Dashboard > Guest Reviews**
2. Click **+ Add Review**
3. Fill in:
   - Guest Name (required)
   - Review Text (required)
   - Star Rating (1-5, default 5)
   - Source (Google, Airbnb, Booking.com, Direct, Other)
   - Stay Date (optional)
   - Guest Photo (optional)
   - Display Order (controls position in reviews grid)
   - Publish this review (checkbox to activate)
4. Click **Save Review**

## Google Business Profile Integration

### Important Notes

⚠️ **Official API Only**: This feature is designed to work with Google's official Business Profile API. **Do NOT scrape Google Maps or Google Search results** - this violates Google's Terms of Service.

### Setup Instructions (Future Implementation)

1. **Get Google API Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the "Google My Business API" (or successor)
   - Create OAuth 2.0 credentials

2. **Configure Environment**
   - Add to your `.env` file:
   ```
   GOOGLE_BUSINESS_API_KEY=your_api_key_here
   GOOGLE_BUSINESS_LOCATION_ID=your_location_id_here
   ```

3. **Automatic Sync** (When implemented)
   - Reviews will automatically sync from Google Business Profile
   - Only approved reviews will be displayed
   - Sync happens on a scheduled basis

### Manual Review Entry (Current Method)

If you cannot use the Google API yet:

1. Copy reviews directly from your Google Business Profile or Google Maps listing
2. Use the Admin Dashboard to manually add each review
3. Set source to "Google Reviews"
4. Mark as active to display on website

## Usage

### On the Website

**Location**: Reviews section appears above the "Ready for Your Escape?" call-to-action button

**Display**:
- Average rating with stars (★)
- Total review count
- 3 featured reviews in a grid
- "View More Reviews" button (if more than 3 reviews exist)

**Clicking "View More Reviews"**:
- Opens a modal window
- Shows all active reviews
- Visitors stay on your website
- Modal can be closed with X button or ESC key

### In the Admin Dashboard

**Access**: Admin Dashboard → Guest Reviews

**Available Actions**:
- **Filter**: By source, rating, status
- **Search**: By guest name or review text
- **Add**: Create new review manually
- **Edit**: Modify existing review details
- **Delete**: Remove review permanently
- **Toggle Status**: Activate/deactivate without deleting
- **Reorder**: Change display_order to control position

## Review Display Logic

### Order on Website

1. Reviews display in order of `display_order` field (ascending)
2. For same display_order, newer reviews appear first (by ID)
3. Only `active=True` reviews are shown to visitors
4. Featured reviews: First 3 active reviews are shown initially

### Average Rating Calculation

- Automatically calculated from all active reviews
- Updated in real-time as reviews are added/modified
- Displayed with one decimal place (e.g., 4.6 / 5)

## File Structure

### New/Modified Files

```
E:\My Software Backup\teahousevilla\
├── bookings/
│   ├── views.py (Added reviews management views)
│   └── admin_urls.py (Added reviews URLs)
├── property/
│   ├── views.py (Updated home view + API endpoint)
│   └── urls.py (Added api/reviews endpoint)
├── templates/
│   ├── admin_dashboard/
│   │   ├── base.html (Added Reviews link to sidebar)
│   │   ├── reviews_list.html (NEW)
│   │   └── review_form.html (NEW)
│   ├── property/
│   │   └── home.html (Added reviews section)
│   └── base.html (Added reviews.js script)
├── static/
│   ├── css/
│   │   ├── frontend.css (Added reviews styling)
│   │   └── admin-dashboard.css (Added form styling)
│   └── js/
│       └── reviews.js (NEW - Reviews interactivity)
└── GUEST_REVIEWS_SETUP.md (This file)
```

## API Endpoints

### Get All Active Reviews (JSON)

```
GET /api/reviews/
```

**Response**:
```json
{
  "success": true,
  "count": 12,
  "reviews": [
    {
      "id": 1,
      "guest_name": "John Doe",
      "rating": 5,
      "review_text": "Amazing stay!",
      "source": "google",
      "stay_date": "2024-08-15",
      "guest_photo": "https://example.com/photo.jpg"
    }
  ]
}
```

## Customization

### Styling

Edit `static/css/frontend.css` to customize:
- Review card colors and shadows
- Star color (currently `var(--villa-brass)`)
- Modal styling
- Responsive breakpoints

Example color variables:
```css
--villa-forest: #1f3a2e (dark green)
--villa-brass: #b89b5e (gold)
--villa-cream: #f7f4ed (warm cream)
```

### Number of Featured Reviews

Edit `property/views.py`:
```python
"featured_reviews": active_reviews[:3],  # Change 3 to desired number
```

### Modal Behavior

Edit `static/js/reviews.js`:
- Line ~50: Modify `loadAllReviews()` for custom loading behavior
- Line ~80: Change animation timing/style
- Line ~115: Modify review card rendering HTML

## Troubleshooting

### Reviews Not Showing on Website

1. **Check Status**: Verify reviews have `active=True` in admin
2. **Check Count**: Ensure at least one active review exists
3. **Check Cache**: Clear browser cache and hard refresh
4. **Check Console**: Open browser DevTools (F12) and check console for errors

### Modal Not Opening

1. **Check JavaScript**: Ensure `reviews.js` is loaded (check Network tab in DevTools)
2. **Check Permissions**: Verify CSRF token is included in forms
3. **Check Endpoint**: Try accessing `/api/reviews/` directly in browser

### Photos Not Displaying

1. **Check Upload**: Verify photo was uploaded in admin
2. **Check Cloudinary**: If using Cloudinary storage, verify configuration
3. **Check URL**: Inspect element and check image URL in Network tab

## Performance Notes

- Reviews are cached at the page level (Django template caching)
- API endpoint is lightweight and returns only necessary data
- JavaScript modal doesn't reload page (AJAX loading)
- Responsive images optimize mobile performance

## Security

- ✅ XSS Protection: Review text is escaped in JavaScript
- ✅ CSRF Protection: Forms include CSRF token
- ✅ Authentication: Admin functions require staff login
- ✅ Authorization: Only staff can manage reviews
- ✅ Data Validation: All inputs are validated server-side

## Support & Future Enhancements

### Planned Features

1. **Google API Integration** - Automatic review sync from Google Business Profile
2. **Review Verification Badge** - Show which reviews are verified purchases
3. **Review Analytics** - Track which reviews get most engagement
4. **Email Notifications** - Notify owner when new reviews appear
5. **Multi-language Support** - Display reviews in multiple languages
6. **Review Pagination** - Navigate through reviews in modal
7. **Export Reviews** - Backup reviews as CSV or JSON

### Reporting Issues

If you encounter issues:
1. Check this documentation first
2. Review browser console for JavaScript errors
3. Check Django logs for server errors
4. Verify all URLs and permissions are configured correctly

## Contact & Updates

For the latest documentation and updates, refer to:
- Django project README.md
- GitHub repository (if applicable)
- Support documentation at teahousevillagalle.com

---

**Last Updated**: September 7, 2026
**Version**: 1.0.0
**Status**: Production Ready
