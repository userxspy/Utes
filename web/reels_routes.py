import logging
from aiohttp import web
from database.ia_filterdb import reels
from web.web_assets import get_auth

logger = logging.getLogger(__name__)
reels_routes = web.RouteTableDef()

# ─────────────────────────────────────────────────────────
# 🎬 REELS FRONTEND (INSTAGRAM / TIKTOK STYLE)
# ─────────────────────────────────────────────────────────
REELS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Shorts & Reels</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'DM Sans', sans-serif; }
        body { background: #000; color: #fff; overflow: hidden; }
        
        /* 📱 Top Navigation (Back Button) */
        .top-nav {
            position: absolute; top: 20px; left: 20px; z-index: 999;
            display: flex; align-items: center; gap: 10px;
        }
        .back-btn {
            background: rgba(0,0,0,0.5); backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1); color: #fff;
            width: 40px; height: 40px; border-radius: 50%;
            display: flex; justify-content: center; align-items: center;
            text-decoration: none; font-size: 20px;
        }
        
        /* 🎬 Scroll Snap Magic */
        .reels-container {
            height: 100vh; width: 100vw;
            overflow-y: scroll; scroll-snap-type: y mandatory;
            scroll-behavior: smooth; -ms-overflow-style: none; scrollbar-width: none;
        }
        .reels-container::-webkit-scrollbar { display: none; }

        /* 🎞️ Individual Reel Box */
        .reel {
            position: relative; height: 100vh; width: 100vw;
            scroll-snap-align: start; scroll-snap-stop: always;
            display: flex; justify-content: center; align-items: center; background: #050505;
        }
        
        video {
            height: 100%; width: 100%; object-fit: cover; /* Fills screen perfectly */
        }

        /* 📝 Overlay Details (Bottom) */
        .overlay {
            position: absolute; bottom: 20px; left: 15px; right: 70px; z-index: 10;
            background: linear-gradient(to top, rgba(0,0,0,0.9), transparent);
            padding: 30px 10px 10px; border-radius: 12px; pointer-events: none;
        }
        .username { font-weight: 700; font-size: 15px; display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
        .verified { color: #00d2c4; font-size: 14px; }
        .caption { font-size: 14px; font-weight: 400; line-height: 1.4; margin-bottom: 5px; text-shadow: 0 1px 3px rgba(0,0,0,0.8); }
        .hashtags { color: #00d2c4; font-size: 13px; font-weight: 600; }
        
        /* 🎛️ Action Buttons (Right) */
        .actions {
            position: absolute; right: 15px; bottom: 30px; z-index: 10;
            display: flex; flex-direction: column; gap: 20px; align-items: center;
        }
        .action-btn {
            background: rgba(0,0,0,0.4); backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.1); color: #fff;
            width: 46px; height: 46px; border-radius: 50%;
            display: flex; justify-content: center; align-items: center;
            font-size: 22px; cursor: pointer; transition: transform 0.2s;
        }
        .action-btn:active { transform: scale(0.9); }
        .action-text { font-size: 12px; font-weight: 600; margin-top: 4px; text-shadow: 0 1px 3px rgba(0,0,0,0.8); }
        .action-item { display: flex; flex-direction: column; align-items: center; }

        /* 🔊 Mute/Unmute Indicator */
        .sound-indicator {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.6); padding: 15px; border-radius: 50%;
            font-size: 30px; display: none; z-index: 20; pointer-events: none;
            animation: fadeOut 1s forwards;
        }
        @keyframes fadeOut { 0% { opacity: 1; transform: translate(-50%, -50%) scale(1); } 100% { opacity: 0; transform: translate(-50%, -50%) scale(1.5); display: none; } }
        
        .loader {
            text-align: center; padding: 20px; color: #888; font-size: 14px; font-weight: bold;
        }
    </style>
</head>
<body>

    <div class="top-nav">
        <a href="/dashboard" class="back-btn">⬅️</a>
    </div>

    <div class="reels-container" id="feed">
        </div>
    
    <div id="loading" class="loader">⏳ Loading more reels...</div>

    <script>
        let page = 1;
        let isLoading = false;
        let hasMore = true;
        const feed = document.getElementById('feed');
        const loadingDiv = document.getElementById('loading');

        // 🎥 Fetch Reels Data from API
        async function loadReels() {
            if (isLoading || !hasMore) return;
            isLoading = true;
            loadingDiv.style.display = 'block';
            
            try {
                const res = await fetch(`/api/get_reels?page=${page}&limit=4`);
                const data = await res.json();
                
                if (data.data.length === 0) {
                    hasMore = false;
                    loadingDiv.innerHTML = "No more reels to show! 🎬";
                    return;
                }

                data.data.forEach(reel => {
                    const div = document.createElement('div');
                    div.className = 'reel';
                    div.innerHTML = `
                        <video src="${reel.video_url}" loop muted playsinline preload="metadata"></video>
                        <div class="sound-indicator" id="sound-${reel.id}">🔇</div>
                        <div class="overlay">
                            <div class="username">@FastFinder <span class="verified">✔</span></div>
                            <div class="caption">${reel.caption}</div>
                            <div class="hashtags">${reel.hashtags}</div>
                        </div>
                        <div class="actions">
                            <div class="action-item">
                                <button class="action-btn" onclick="this.innerText='❤️'; this.style.color='#e50914';">🤍</button>
                                <span class="action-text">${reel.views > 0 ? reel.views : 'Like'}</span>
                            </div>
                            <div class="action-item">
                                <button class="action-btn" onclick="shareReel('${reel.video_url}')">↗️</button>
                                <span class="action-text">Share</span>
                            </div>
                        </div>
                    `;
                    feed.appendChild(div);
                });
                
                page++;
                setupObserver(); // Re-attach observer to new videos
            } catch (err) {
                console.error("Failed to load reels:", err);
            } finally {
                isLoading = false;
                if(hasMore) loadingDiv.style.display = 'none';
            }
        }

        // 👁️ Auto-Play Magic (Intersection Observer)
        function setupObserver() {
            const videos = document.querySelectorAll('video');
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        // Play if fully visible
                        entry.target.play().catch(e => console.log("Autoplay blocked:", e));
                    } else {
                        // Pause & Reset if swiped away
                        entry.target.pause();
                        entry.target.currentTime = 0;
                    }
                });
            }, { threshold: 0.7 }); // 70% video must be on screen to trigger

            videos.forEach(video => {
                observer.observe(video);
                
                // 🔊 Tap to Unmute/Mute Logic
                video.onclick = function() {
                    video.muted = !video.muted;
                    let indicator = video.nextElementSibling;
                    indicator.innerText = video.muted ? "🔇" : "🔊";
                    indicator.style.display = "block";
                    indicator.style.animation = 'none';
                    indicator.offsetHeight; /* trigger reflow */
                    indicator.style.animation = null; 
                };
            });
        }

        // 🔄 Infinite Scrolling
        feed.addEventListener('scroll', () => {
            if (feed.scrollTop + feed.clientHeight >= feed.scrollHeight - 300) {
                loadReels();
            }
        });

        // ↗️ Share Function
        function shareReel(url) {
            const fullUrl = window.location.origin + url;
            if (navigator.share) {
                navigator.share({ title: 'Fast Finder Reel', url: fullUrl });
            } else {
                navigator.clipboard.writeText(fullUrl);
                alert("Link copied to clipboard!");
            }
        }

        // Initial Load
        loadReels();
    </script>
</body>
</html>"""

# ─────────────────────────────────────────────────────────
# 🌐 WEB PAGE ROUTE
# ─────────────────────────────────────────────────────────
@reels_routes.get('/reels')
async def reels_page(req):
    role, _ = await get_auth(req)
    if not role:
        return web.HTTPFound('/login')
    # सीधे HTML सर्व करें (बिना Navbar के, फुल स्क्रीन एक्सपीरियंस के लिए)
    return web.Response(text=REELS_HTML, content_type='text/html')

# ─────────────────────────────────────────────────────────
# ⚙️ API ROUTE (FETCH DATA FROM DB)
# ─────────────────────────────────────────────────────────
@reels_routes.get('/api/get_reels')
async def api_get_reels(req):
    role, _ = await get_auth(req)
    if not role: return web.json_response({"error": "Unauthorized"}, status=403)
    
    try:
        page = int(req.query.get('page', 1))
        limit = int(req.query.get('limit', 4))
        skip = (page - 1) * limit
        
        # ताज़ा रील्स सबसे पहले लाएं
        cursor = reels.find({}).sort("added_date", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        
        data = []
        for d in docs:
            # हैशटैग्स को स्ट्रिंग में बदलें
            hashtags_str = " ".join(d.get('hashtags', []))
            caption = d.get('caption', '').replace(hashtags_str, '').strip()
            
            data.append({
                "id": str(d.get('_id', '')),
                "message_id": d.get('message_id'),
                "caption": caption if caption else "Fast Finder Shorts 🔥",
                "hashtags": hashtags_str,
                "views": d.get('views', 0),
                "video_url": f"/download/{d.get('message_id')}" # डायरेक्ट स्ट्रीम URL
            })
            
        return web.json_response({"success": True, "data": data})
        
    except Exception as e:
        logger.error(f"Reels API Error: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)
