# Tea House Villa - Property Admin Quick Guide

A quick reference for managing villa details through the admin panel.

---

## Access Admin Panel

1. Go to: `https://teahousevillagalle.com/admin/`
2. Login with your admin credentials
3. You'll see the admin dashboard

---

## Main Property Settings

### Navigate to Property Details

**Admin Home** → **Property** → **Teahouse Villa**

---

## Editing Property Information

### Basic Information
- **Name**: Tea House Villa (property name)
- **Tagline**: "A slower kind of luxury"
- **Short Description**: Used in search results and homepage
- **Full Description**: Detailed property overview (supports Markdown)

### Property Capacity
- **Max Guests**: 15
- **Bedrooms**: 4
- **Bathrooms**: 3
- **Property Size**: 353 m²

### Check-in/Check-out
- **Check-in Time**: 2:00 PM (14:00)
- **Check-out Time**: 11:00 AM (11:00)

### Hero Section
- **Hero Image**: Upload villa cover photo (recommended: 1920x1080px)
- **Hero Video URL**: Optional YouTube/Vimeo video (will auto-play as background)

### Contact Information
- **Phone Number**: +94 (country code required)
- **WhatsApp Number**: 94771234567 (digits only, no spaces)
- **Email**: contact@teahousevilla.com

### House Rules & Policies
- **House Rules**: Write rules (Markdown supported). Example:
  ```
  - No smoking
  - No loud noise after 10 PM
  - Respect the garden
  ```
- **Cancellation Policy**: Write policy details

### Social Media & Booking Platforms
- **Facebook URL**: https://facebook.com/teahousevilla
- **Instagram URL**: https://instagram.com/teahousevilla
- **TikTok URL**: https://tiktok.com/@teahousevilla
- **YouTube URL**: https://youtube.com/teahousevilla
- **Airbnb URL**: https://airbnb.com/rooms/...
- **Booking.com URL**: https://booking.com/...

---

## Adding Property Amenities

### Navigate to Amenities Section
In Property edit page, scroll down to **Amenities** section.

### Add New Amenity

1. Click **"Add another Amenity"** button
2. Fill in fields:

**Name**: (e.g., "Free Wi-Fi")
- Common names: Free Wi-Fi, Air Conditioning, Pool, BBQ Facilities, TV, Washing Machine, etc.

**Category**: (select from dropdown)
- General Amenities
- Kitchen
- Bathroom
- Bedroom
- Outdoor
- Entertainment
- Comfort & Convenience

**Icon**: Bootstrap Icons class
- Examples: `bi-wifi` (Wi-Fi), `bi-snow` (AC), `bi-cup` (Tea), `bi-fire` (Fireplace)
- Full list: https://icons.getbootstrap.com/
- Just use the class name (e.g., `bi-wifi`, not the full HTML)

**Description**: Optional details
- Example: "High-speed fiber internet throughout the villa"

**Display Order**: Number for ordering in UI
- Lower numbers appear first (0, 1, 2, 3, ...)

**Active**: Checkbox
- ✓ Check to show amenity
- ☐ Uncheck to hide

3. Click **Save**

---

## Managing Property Views

### Navigate to Views Section
In Property edit page, scroll down to **Views** section.

### Add Property View

1. Click **"Add another View"** button
2. Fill in fields:

**View Type**: (select from dropdown)
- Garden View
- Pool View
- Mountain View
- Countryside View
- Landmark View
- Inner Courtyard View

**Description**: Optional details about the view
- Example: "Lush tropical garden with sunset colors"

**Display Order**: Number (lower = first)

**Active**: Checkbox to show/hide

3. Click **Save**

---

## Managing Bedroom Details

### Navigate to Rooms List
**Admin Home** → **Rooms** → (select room)

### Edit Room Details

**Name**: Bedroom name (e.g., "Master Bedroom", "Guest Bedroom 1")

**Capacity**: Max guests (e.g., 2, 4)

**Bed Type**: Legacy field - use BedConfiguration instead (leave as-is or update)

**Bathroom Info**: Number/type of bathrooms (e.g., "1 ensuite bathroom")

**Has AC**: Check if room has air conditioning

**Size**: Room size in m² (e.g., 45)

**Description**: Room details (Markdown supported). Example:
```
A spacious master suite with king bed and ensuite bathroom.
Features a private balcony overlooking the garden.
```

**Facilities**: Select amenities for this room
- Hold Ctrl to select multiple

---

## Adding Bed Configurations

### In Room Edit Page, Scroll to "BED CONFIGURATIONS"

This tells guests exactly what beds are in the room.

### Add Bed Configuration

1. Click **"Add another Bed Configuration"** button
2. Fill in:

**Bed Type**: (select from dropdown)
- Queen
- Double
- Twin
- Bunk
- Single
- Sofa Bed
- Crib

**Quantity**: How many of this bed type
- Example: Bedroom 3 has "2 Queen" beds → Quantity: 2

**Display Order**: Order in UI
- 1, 2, 3... (lower appears first)

**Active**: Checkbox to show/hide

3. Click **Save**

### Example Configurations:
- **Bedroom 1** (Master): 1x Queen
- **Bedroom 2** (Double): 1x Queen
- **Bedroom 3** (Family): 2x Queen
- **Bedroom 4** (Kids): 2x Bunk

---

## Adding Room Amenities

Room amenities appear on room detail pages.

### In Room Edit Page, Scroll to "FACILITIES"

1. Hold **Ctrl** (Windows) or **Cmd** (Mac)
2. Click amenities to select multiple
3. Click **Save**

Examples:
- "Free Wi-Fi"
- "Air Conditioning"
- "Work Desk"
- "TV"
- "Private Bathroom"

---

## Managing Room Photos

### In Room Edit Page, Scroll to "MEDIA" Section

### Add Room Photo

1. Click **"Add another Media"** button
2. Fill in:

**Media Type**: Image (select from dropdown)

**Image**: Click to upload room photo
- Recommended size: 1200x800px or larger
- Formats: JPG, PNG (images auto-resize to max 1920px)

**Caption**: Photo description (e.g., "Master bedroom with balcony")

**Category**: 
- Bedrooms (for room detail pages)
- Or: Villa, Bathrooms, Pool, Kitchen, Garden, Exterior, Nearby

**Is Cover**: Checkbox
- ✓ Mark ONE image as cover (this appears on room cards)

**Display Order**: Number (lower = first)

**Active**: Checkbox to show/hide

3. Click **Save**

**Important**: Only ONE image per room should be marked as "Cover" (show on room listing page).

---

## Managing Pricing

### Navigate to Prices Section
In Property edit page, scroll to **Prices** section.

### Add Price

1. Click **"Add another Price"** button
2. Fill in:

**Price Type**: (select from dropdown)
- **Standard Rate**: Default daily rate (always active)
- **Weekend Rate**: Friday-Sunday
- **Peak Season Rate**: Holiday periods
- **Off-Season Rate**: Low season discounts
- **Special Offer**: Limited-time promotion

**Start Date**: When price becomes active (leave blank for always-on)

**End Date**: When price expires (leave blank for indefinite)

**Amount**: Price per night (e.g., 250.00 for $250/night)

**Notes**: Optional internal notes

**Active**: Checkbox to enable/disable

3. Click **Save**

### Example Setup:
```
Standard Rate: $250/night (always on)
Weekend Rate: $300/night (Fri-Sun)
Peak Season: $350/night (Dec 15 - Jan 5)
Off-Season: $180/night (May-Aug)
```

---

## SEO Settings (Search Engines & Social Media)

### Navigate to SEO Section
In Property edit page, scroll to **SEO** section (click to expand).

### SEO Fields

**SEO Title**: (max 60 characters)
- Used in Google search results
- Example: `Tea House Villa Galle | Private 4-Bedroom Villa with Pool`

**SEO Description**: (max 160 characters)
- Used in Google search results
- Example: `Stay at Tea House Villa in Galle - spacious 4-bedroom private villa with infinity pool, tropical garden, perfect for families and groups.`

**SEO Canonical URL**: (leave blank for auto-generation)
- Advanced: use if property is listed on multiple domains

**OG Image**: Upload custom social media preview image
- Recommended size: 1200x630px
- Used when property link shared on Facebook, WhatsApp, etc.
- Leave blank to use hero image

### Leave Blank for Auto-Generation
If you leave SEO fields blank:
- Title auto-generates as: `"Tea House Villa Galle | Private 4-Bedroom Villa"`
- Description uses your "Short Description" field

---

## Managing Media/Gallery

### Navigate to Media List
**Admin Home** → **Media**

### Upload Gallery Image

1. Click **"Add Media"** button
2. Fill in:

**Villa**: (should be pre-filled: Teahouse Villa)

**Room**: (leave blank for villa-wide, or select room)

**Media Type**: Image (select from dropdown)

**Image**: Click to upload photo
- Recommended size: 1200x800px or larger

**Caption**: Photo description
- Used for alt text (SEO, accessibility)

**Category**: (select from dropdown)
- Villa (general villa photos)
- Bedrooms
- Bathrooms
- Swimming Pool
- Kitchen
- Garden
- Exterior
- Nearby Attractions
- Dining
- Living Room

**Is Cover**: Checkbox
- ✓ Mark as cover image for room (only 1 per room)

**Display Order**: Number (lower = first)

**Active**: Checkbox to show/hide

3. Click **Save**

### Important
- Only upload actual photos, don't reupload existing images when editing
- Use descriptive captions for SEO and accessibility
- Use appropriate categories for gallery organization

---

## Managing Attractions

### Navigate to Attractions
**Admin Home** → **Attractions**

### Add Nearby Attraction

1. Click **"Add Attraction"** button
2. Fill in:

**Villa**: Teahouse Villa (pre-filled)

**Name**: Attraction name
- Examples: "Galle Fort", "Mirissa Beach", "Whale Watching", "Spice Garden"

**Category**: (select from dropdown)
- Beach
- Restaurant
- Landmark
- Activity
- Shopping
- Other

**Distance Text**: How far from villa
- Examples: "2 km away", "5 min drive", "15 min walk"

**Description**: Details about attraction
- Example: "Historic 16th-century fort with stunning coastal views"

**Image**: Optional photo of attraction

**Google Maps URL**: Direct link to location on Maps
- Example: `https://maps.google.com/?q=Galle+Fort`

**Display Order**: Number (lower = first)

**Active**: Checkbox to show/hide

3. Click **Save**

---

## Managing Guest Reviews

### Navigate to Testimonials
**Admin Home** → **Testimonials**

### Add Guest Review

1. Click **"Add Testimonial"** button
2. Fill in:

**Villa**: Teahouse Villa (pre-filled)

**Guest Name**: Guest's name
- Example: "John Smith"

**Rating**: (select from dropdown)
- 1 Star to 5 Stars

**Review Text**: What guest wrote
- Example: "Beautiful villa, amazing staff, great location! Would return."

**Source**: Where review came from
- Google Reviews
- Airbnb
- Booking.com
- Direct Guest (direct booking)
- Other

**Stay Date**: When guest stayed
- Helps show review date to visitors

**Guest Photo**: Optional guest photo (with permission)

**Display Order**: Number (lower = first)

**Active**: Checkbox to show/hide

3. Click **Save**

---

## Making Changes & Preview

### Save Changes
After editing property details:
1. Scroll to bottom of form
2. Click **"Save"** button (or **"Save and continue editing"**)

### Preview Website
After saving:
1. Visit: https://teahousevillagalle.com/property/
2. Refresh page (Ctrl+F5 to clear cache)
3. Scroll through and verify all details are correct

---

## Common Tasks Checklist

### Initial Setup
- [ ] Fill in all Property details
- [ ] Add 4 bedrooms with bed configurations
- [ ] Upload hero image
- [ ] Upload room photos (mark covers)
- [ ] Add 6-8 key amenities
- [ ] Configure check-in/out times
- [ ] Add house rules & cancellation policy
- [ ] Set up pricing
- [ ] Fill in contact information

### Content Maintenance
- [ ] Update room descriptions quarterly
- [ ] Add new guest reviews as received
- [ ] Refresh gallery images seasonally
- [ ] Update pricing for peak/off-season
- [ ] Keep social media links current

### SEO Optimization
- [ ] Write compelling SEO title
- [ ] Write engaging meta description
- [ ] Upload 1200x630px social preview image
- [ ] Ensure room descriptions are detailed
- [ ] Add meaningful captions to photos

---

## Troubleshooting

### Images Not Showing
- Check image size (recommended: 1200px+ width)
- Verify image format is JPG or PNG
- Check "Active" checkbox is enabled
- Clear browser cache (Ctrl+Shift+Delete)

### Changes Not Appearing on Website
- Click **Save** in admin (not just navigate away)
- Clear browser cache (Ctrl+Shift+Delete)
- Wait up to 5 minutes for CDN refresh
- Check if images are on Cloudinary (not local server)

### Room Amenities Not Showing
- In Room edit, scroll to Facilities section
- Hold Ctrl and select amenities
- Click Save
- Refresh website

### Bed Configuration Not Showing
- In Room edit, scroll to "Bed Configurations"
- Verify beds are marked "Active"
- Check Display Order (should be 1, 2, 3...)
- Click Save

### SEO Title Not Showing in Google
- Fill in "SEO Title" field in admin
- Google takes 1-2 weeks to re-crawl
- Check title in page source (right-click → View Page Source)

---

## Getting Help

For technical issues:
1. Check this guide first
2. Contact development team
3. Include specific error messages or screenshots

---

**Last Updated**: September 2026  
**Property Name**: Tea House Villa  
**Admin URL**: `/admin/`
