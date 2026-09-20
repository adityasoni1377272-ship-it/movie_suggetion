import warnings
warnings.filterwarnings("ignore")

import os
import requests
import streamlit as st
from st_keyup import st_keyup
import random
import time

# =============================
# CONFIG
# =============================
API_BASE = os.getenv("API_BASE", "https://movie-rec-466x.onrender.com")
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(page_title="Moovieez", page_icon="🎬", layout="wide")

# Hide Streamlit chrome
st.markdown("""
    <style>
    #MainMenu, header, footer, .stAppDeployButton, .stStatusWidget, [data-testid="stStatusWidget"] {visibility: hidden; height: 0;}
    .block-container {padding-top: 0.5rem; max-width: 1400px;}
    [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"], .st-key-search + div {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# Initialize state
defaults = {"dark_mode": True, "view": "home", "selected_tmdb_id": None, "watchlist": [], "recently_viewed": [], "random_movie": None}
for key, val in defaults.items():
    if key not in st.session_state:
        setattr(st.session_state, key, val)

# Skeleton Loading States (Global)
if "loading_state" not in st.session_state:
    st.session_state.loading_state = {}
if "cached_data" not in st.session_state:
    st.session_state.cached_data = {}

# Navigation
def goto(page, id=None):
    st.session_state.view = page
    st.session_state.selected_tmdb_id = id

def toggle_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode

def add_watchlist(movie_id, title, poster):
    if movie_id not in [m["id"] for m in st.session_state.watchlist]:
        st.session_state.watchlist.append({"id": movie_id, "title": title, "poster_url": poster})
        st.toast(f"✅ Added '{title}'!")

def remove_watchlist(movie_id, title=""):
    st.session_state.watchlist = [m for m in st.session_state.watchlist if m["id"] != movie_id]

def add_recently_viewed(movie_id, title, poster_url):
    st.session_state.recently_viewed = [m for m in st.session_state.recently_viewed if m["id"] != movie_id]
    st.session_state.recently_viewed.insert(0, {"id": movie_id, "title": title, "poster_url": poster_url})
    st.session_state.recently_viewed = st.session_state.recently_viewed[:5]

def pick_random_movie():
    movies = st.session_state.watchlist if st.session_state.watchlist else []
    if not movies:
        data = api_get("/home", {"category": "popular", "limit": 50})
        if data:
            results = data if isinstance(data, list) else data.get("results", [])
            movies = [{"id": m.get("tmdb_id"), "title": m.get("title", "Unknown"), "poster_url": m.get("poster_url")} for m in results if m.get("tmdb_id")]
    if movies:
        st.session_state.random_movie = random.choice(movies)
        st.toast(f"🎲 Random pick: {st.session_state.random_movie['title']}")
        st.rerun()
    else:
        st.toast("❌ No movies available!")

# =============================
# THEME & SKELETON CSS
# =============================
def get_styles():
    d1, d2 = "#39FF14", "#1A7A0A"
    l1, l2 = "#6DF374", "#126017"
    black = "#010500"
    
    if st.session_state.dark_mode:
        bg, text, sidebar_bg, border, accent, card_bg = black, "#FFFFFF", "#1A3A0A", "#436B00", d1, "#080C05"
        genre_bg, genre_text, genre_border = "rgba(57,255,20,0.15)", d1, d1
        g1, g2, btn_text = d1, d2, black
        sub_color, rating_color, slider_color = d1, d1, d1
        shadow, hover_shadow = "0 2px 8px rgba(57,255,20,0.2)", "0 4px 15px rgba(57,255,20,0.3)"
        sidebar_text, feed_text, heading = "#FFFFFF", "#FFFFFF", "#FFFFFF"
        skeleton_color = "#1A2A1A"
        skeleton_shine = "linear-gradient(90deg, #1A2A1A 25%, #2A3A2A 50%, #1A2A1A 75%)"
    else:
        bg, text, sidebar_bg, border, accent, card_bg = "#FAFCF8", "#1B1B1B", l2, "#C8E6C9", l1, "#FFFFFF"
        genre_bg, genre_text, genre_border = "rgba(27,94,32,0.10)", l2, l2
        g1, g2, btn_text = l1, l2, "#FFFFFF"
        sub_color, rating_color, slider_color = l1, l1, l2
        shadow, hover_shadow = "0 2px 8px rgba(18,96,23,0.2)", "0 4px 15px rgba(18,96,23,0.3)"
        sidebar_text, feed_text, heading = "#FFFFFF", "#1B1B1B", "#1B1B1B"
        skeleton_color = "#E0E0E0"
        skeleton_shine = "linear-gradient(90deg, #E0E0E0 25%, #F0F0F0 50%, #E0E0E0 75%)"

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
    * {{font-family:'Poppins',sans-serif;}}
    .stApp, .stAppViewContainer {{background-color:{bg}!important;}}
    .stDeployButton, .stStatusWidget {{display:none!important;}}

    .header {{
        background:{card_bg}; border:1px solid {border}; padding:1rem 2rem; border-radius:20px;
        margin-bottom:2rem; display:flex; align-items:center; justify-content:space-between;
        box-shadow:0 2px 10px rgba(0,0,0,0.05);
    }}
    .logo-icon {{font-size:2.5rem; background:{accent}; color:{bg}; padding:0.2rem 0.8rem; border-radius:14px;}}
    .logo-text h1 {{color:{text}!important; font-size:2rem!important; font-weight:800!important; margin:0!important; letter-spacing:2px;}}
    .subtitle {{color:{sub_color}; font-size:0.7rem; letter-spacing:3px; opacity:0.8;}}

    .stSidebar {{
        background:{sidebar_bg}!important; border-right:1px solid {border}!important;
    }}
    .stSidebar .stMarkdown, .stSidebar label, .stSidebar .stRadio,
    .stSidebar .stSelectbox label, .stSidebar .stSlider label {{
        color:{sidebar_text}!important;
    }}
    .stSidebar .stButton > button, .stButton > button {{
        background:linear-gradient(135deg,{g1},{g2})!important;
        color:{btn_text}!important; border:none!important; border-radius:30px!important;
        font-weight:700!important; width:100%; padding:0.4rem 0.8rem!important;
        transition:all 0.3s ease!important; box-shadow:{shadow}!important; cursor:pointer!important;
    }}
    .stSidebar .stButton > button:hover, .stButton > button:hover {{
        transform:scale(1.03)!important; box-shadow:{hover_shadow}!important;
    }}
    .stSidebar .stButton > button:active, .stButton > button:active {{
        transform:scale(0.97)!important;
    }}

    .movie-card {{
        background:{card_bg}!important; border:1px solid {border}!important;
        border-radius:16px!important; padding:12px!important; text-align:center; height:100%;
        transition:all 0.3s ease; box-shadow:0 2px 8px rgba(0,0,0,0.04);
    }}
    .movie-card:hover {{
        transform:translateY(-5px); border-color:{accent}!important;
        box-shadow:0 8px 25px rgba(0,0,0,0.15);
    }}
    .movie-card img {{border-radius:12px!important; width:100%; aspect-ratio:2/3; object-fit:cover;}}
    .movie-title {{font-size:0.9rem; font-weight:600; margin-top:0.6rem; color:{text}; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}}
    .movie-rating {{color:{rating_color}; font-size:0.85rem; font-weight:600; margin:0.3rem 0;}}

    .genre-tag {{
        background:{genre_bg}; color:{genre_text}!important; border:1px solid {genre_border};
        padding:4px 14px; border-radius:20px; font-size:0.75rem; margin:3px; display:inline-block;
        font-weight:500; transition:all 0.2s ease;
    }}
    .genre-tag:hover {{transform:scale(1.05); box-shadow:0 2px 8px rgba(0,0,0,0.1);}}

    div[data-testid="stSlider"] div[class*="stSlider"] div[role="slider"] {{
        background:{slider_color}!important; border-color:{slider_color}!important;
    }}
    div[data-testid="stSlider"] div[class*="stSlider"] div[class*="innerTrack"] {{
        background:{slider_color}!important;
    }}

    .stRadio label, .stRadio div, .stRadio span, .stRadio [role="radiogroup"] label {{
        color:{feed_text}!important; font-weight:500;
    }}

    .section-title {{
        font-size:1.8rem; font-weight:700; margin-bottom:1.5rem;
        color:{heading}; border-left:5px solid {accent}; padding-left:1rem;
    }}
    h1,h2,h3,h4,h5,h6,.stMarkdown h1,.stMarkdown h2,.stMarkdown h3 {{color:{text}!important;}}
    hr {{border-color:{border}!important; opacity:0.3;}}
    .footer {{text-align:center; padding:1rem; margin-top:2rem; border-top:1px solid {border}; color:#888; font-size:0.7rem;}}
    .stInfo, .stCaption, .stMarkdown p, .stMarkdown div {{color:{text}!important;}}

    /* SKELETON LOADING STYLES */
    .skeleton {{
        background: {skeleton_color};
        border-radius: 12px;
        margin-bottom: 10px;
        animation: shimmer 1.5s infinite linear;
        background: {skeleton_shine};
        background-size: 200% 100%;
    }}
    .skeleton-poster {{
        width: 100%;
        aspect-ratio: 2/3;
        border-radius: 12px;
    }}
    .skeleton-text {{
        height: 16px;
        width: 80%;
        margin: 8px auto;
        border-radius: 8px;
    }}
    .skeleton-text-small {{
        height: 14px;
        width: 40%;
        margin: 8px auto;
        border-radius: 8px;
    }}
    .skeleton-btn {{
        height: 30px;
        width: 100%;
        border-radius: 30px;
        margin-top: 8px;
    }}

    @keyframes shimmer {{
        0% {{ background-position: -200% 0; }}
        100% {{ background-position: 200% 0; }}
    }}
    ::-webkit-scrollbar {{width:8px; height:8px;}}
    ::-webkit-scrollbar-track {{background:{bg};}}
    ::-webkit-scrollbar-thumb {{background:{accent}; border-radius:10px;}}
    ::-webkit-scrollbar-thumb:hover {{background:{g1};}}

    .watchlist-count {{
        background:{accent}; color:{bg}; padding:0px 8px; border-radius:12px;
        font-size:0.7rem; font-weight:700; margin-left:5px;
    }}
    </style>
    """
st.markdown(get_styles(), unsafe_allow_html=True)

# Header
st.markdown(f"""
    <div class="header">
        <div style="display:flex; align-items:center; gap:15px;">
            <span class="logo-icon">🎬</span>
            <div class="logo-text">
                <h1>MOOVIEEZ</h1>
                <div class="subtitle">✦ DISCOVER · WATCH · REPEAT ✦</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎬 Menu")
    st.button("🏠 Home", on_click=lambda: goto("home"))
    
    wl_count = len(st.session_state.watchlist)
    watchlist_label = f"📋 Watchlist ({wl_count})" if wl_count > 0 else "📋 Watchlist"
    st.button(watchlist_label, on_click=lambda: goto("watchlist"))
    
    st.button("🕐 Recently Viewed", on_click=lambda: goto("recently_viewed"))
    st.button("🎲 Random Movie", on_click=lambda: goto("random"))
    st.button("ℹ️ About", on_click=lambda: goto("about"))
    
    st.divider()
    st.button("☀️ Light" if st.session_state.dark_mode else "🌙 Dark", on_click=toggle_mode)
    st.divider()
    
    st.markdown("### 📺 Feed")
    cats = {"trending": "🔥 Trending", "popular": "⭐ Popular", "top_rated": "🏆 Top Rated", "now_playing": "🎬 Now Playing", "upcoming": "📅 Upcoming"}
    selected_label = st.radio("", list(cats.values()), index=0, label_visibility="collapsed")
    home_category = {v: k for k, v in cats.items()}[selected_label]
    st.divider()
    grid_cols = st.slider("🎯 Columns", 4, 8, 6)

# API Helpers
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        return r.json() if r.status_code < 400 else None
    except requests.RequestException:
        return None


# =============================
# FIXED: Poster URL normalizer
# =============================
def _normalize_poster(url):
    """Normalize poster URL: handle None, relative paths, and full URLs."""
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    if not url:
        return None
    if url.startswith("/"):
        return f"{TMDB_IMG}{url}"
    if url.startswith("http://") or url.startswith("https://"):
        return url
    # bare path without leading slash (e.g. "abc.jpg")
    return f"{TMDB_IMG}/{url.lstrip('/')}"


def show_poster(poster_url, border_radius="12px", fallback_size="3rem"):
    """Render a poster safely without changing the existing card UI."""
    final_url = _normalize_poster(poster_url)

    if final_url:
        try:
            st.image(final_url, use_container_width=True)
            return
        except Exception:
            pass

    st.markdown(
        f"<div style='aspect-ratio:2/3;display:flex;align-items:center;justify-content:center;"
        f"background:rgba(67,107,0,0.2);border-radius:{border_radius};font-size:{fallback_size};'>🎬</div>",
        unsafe_allow_html=True
    )


# =============================
# RENDER FUNCTIONS
# =============================
def render_skeletons(cols=6):
    """Render placeholder skeleton cards"""
    for i in range(0, 12, cols):
        cols_row = st.columns(cols)
        for j, col in enumerate(cols_row):
            with col:
                st.markdown("<div class='movie-card'>", unsafe_allow_html=True)
                st.markdown("<div class='skeleton skeleton-poster'></div>", unsafe_allow_html=True)
                st.markdown("<div class='skeleton skeleton-text'></div>", unsafe_allow_html=True)
                st.markdown("<div class='skeleton skeleton-text-small'></div>", unsafe_allow_html=True)
                st.markdown("<div class='skeleton skeleton-btn'></div>", unsafe_allow_html=True)
                st.markdown("<div class='skeleton skeleton-btn'></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

def render_movies(cards, cols=6, key="grid", show_wl=False):
    if not cards:
        st.info("No recommendations available.")
        return
    for i in range(0, len(cards), cols):
        cols_row = st.columns(cols)
        for j, col in enumerate(cols_row):
            idx = i + j
            if idx >= len(cards):
                break
            m = cards[idx]
            with col:
                st.markdown("<div class='movie-card'>", unsafe_allow_html=True)
                # FIXED: normalize poster using poster_path fallback
                poster = m.get("poster_url") or m.get("poster_path")
                show_poster(poster)
                st.markdown(f"<div class='movie-title'>{m.get('title', 'Untitled')}</div>", unsafe_allow_html=True)
                if m.get("vote_average"):
                    st.markdown(f"<div class='movie-rating'>⭐ {m['vote_average']:.1f}</div>", unsafe_allow_html=True)
                
                if show_wl:
                    in_wl = m["tmdb_id"] in [x["id"] for x in st.session_state.watchlist]
                    if not in_wl:
                        if st.button("➕ Add", key=f"wl_{key}_{idx}", use_container_width=True):
                            add_watchlist(m["tmdb_id"], m.get("title", ""), m.get("poster_url"))
                            st.rerun()
                
                # <--- FIXED ONE-CLICK: Using on_click callback to guarantee the transition
                st.button("▶ Open", key=f"open_{key}_{idx}", use_container_width=True, on_click=lambda mid=m["tmdb_id"], title=m.get("title", "Unknown"), poster=m.get("poster_url"): (
                    add_recently_viewed(mid, title, poster),
                    goto("details", mid)
                ))
                st.markdown("</div>", unsafe_allow_html=True)

# =============================
# PAGE HELPER for LOADING
# =============================
def load_data_with_skeleton(key, fetch_func, cols):
    # Check if we need to load
    if st.session_state.loading_state.get(key, False):
        render_skeletons(cols=cols)
        data = fetch_func()
        st.session_state.cached_data[key] = data
        st.session_state.loading_state[key] = False
        st.rerun()
    elif key not in st.session_state.cached_data:
        st.session_state.loading_state[key] = True
        st.rerun()
    else:
        return st.session_state.cached_data[key]

# =============================
# PAGES
# =============================

# HOME
if st.session_state.view == "home":
    st.markdown('<div class="section-title">🔍 Find Your Next Movie</div>', unsafe_allow_html=True)
    query = st_keyup("", placeholder="Search by title... (e.g., 'deadpool' or 'avatar')", label_visibility="collapsed", debounce=300, key="search")
    
    # SEARCH
    if query and len(query) >= 2:
        data = api_get("/tmdb/search", {"query": query})
        all_results = data.get("results", []) if data else []
        if not all_results:
            dataset_data = api_get("/home", {"category": "popular", "limit": 100})
            if dataset_data:
                results = dataset_data if isinstance(dataset_data, list) else dataset_data.get("results", [])
                for movie in results:
                    if query.lower() in movie.get("title", "").lower():
                        all_results.append(movie)
        if all_results:
            st.markdown(f"### 🎬 Results for '{query}'")
            st.caption(f"✨ Found {len(all_results)} movies")
            cards = [{
                "tmdb_id": m.get("id") or m.get("tmdb_id"),
                "title": m.get("title", "Unknown"),
                "poster_url": (m.get("poster_url") or (f"{TMDB_IMG}{m.get('poster_path')}" if m.get("poster_path") else None)),
                "vote_average": m.get("vote_average")
            } for m in all_results[:50]]
            render_movies(cards, cols=grid_cols, key="search", show_wl=True)
        else:
            st.info(f"No movies found for '{query}'. Try a different search term.")
        st.stop()
    
    # FEED
    st.markdown(f"### {selected_label}")
    if "prev_home_category" not in st.session_state:
        st.session_state.prev_home_category = home_category
    
    # Trigger reload if category changed
    if st.session_state.prev_home_category != home_category:
        st.session_state.cached_data.pop("home_feed", None)
        st.session_state.loading_state.pop("home_feed", None)
        st.session_state.prev_home_category = home_category
        st.rerun()

    def fetch_home():
        return api_get("/home", {"category": home_category, "limit": 24})

    data = load_data_with_skeleton("home_feed", fetch_home, grid_cols)
    if data:
        results = data if isinstance(data, list) else data.get("results", [])
        render_movies(results, cols=grid_cols, key="feed", show_wl=True) if results else st.error("Could not load movies.")
    elif data is None and not st.session_state.loading_state.get("home_feed", False):
        st.error("Could not load movies. Please try again later.")

# ABOUT
elif st.session_state.view == "about":
    st.markdown('<div class="section-title">ℹ️ About Moovieez</div>', unsafe_allow_html=True)
    st.markdown("""
    Moovieez is a full-stack movie recommendation platform designed to make movie discovery simple and enjoyable. 
    Users can search for movies, explore genres, view detailed information, and receive personalized recommendations 
    through a fast, responsive, and modern interface. Built with a focus on performance and user experience, 
    Moovieez showcases the power of full-stack web development and intelligent recommendation systems.
    """)
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🎯 Features**\n- Movie Search\n- Genre Exploration\n- Watchlist Management\n- Recently Viewed\n- Random Movie Picker")
    with col2:
        st.markdown("**⚡ Tech Stack**\n- Frontend: Streamlit\n- Backend: FastAPI\n- Database: TMDB API\n- ML: Recommendation Engine")
    with col3:
        st.markdown("**🎬 About**\n- Version: 1.0.0\n- Made with ❤️\n- © 2026 Moovieez")
    st.divider()
    st.caption("✨ Discover, Watch, Repeat — Your next favorite movie is just a click away!")
    st.button("← Back to Home", on_click=lambda: goto("home"))

# WATCHLIST
elif st.session_state.view == "watchlist":
    st.markdown('<div class="section-title">📋 My Watchlist</div>', unsafe_allow_html=True)
    if not st.session_state.watchlist:
        st.info("🎬 Your watchlist is empty.")
        st.button("← Back", on_click=lambda: goto("home"))
        st.stop()
    
    st.caption(f"🎯 {len(st.session_state.watchlist)} movies saved")
    watchlist_movies = [{"tmdb_id": m["id"], "title": m["title"], "poster_url": m["poster_url"]} for m in st.session_state.watchlist]
    
    # If watchlist exists, we don't need a fetch skeleton, just render directly
    render_movies(watchlist_movies, cols=min(grid_cols, 4), key="wl", show_wl=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.watchlist = []
            st.rerun()
    st.button("← Back", on_click=lambda: goto("home"))

# RECENTLY VIEWED
elif st.session_state.view == "recently_viewed":
    st.markdown('<div class="section-title">🕐 Recently Viewed</div>', unsafe_allow_html=True)
    if not st.session_state.recently_viewed:
        st.info("📭 No movies viewed recently. Start exploring!")
        st.button("← Back", on_click=lambda: goto("home"))
        st.stop()
    
    st.caption(f"🎯 {len(st.session_state.recently_viewed)} movies viewed recently")
    recent_movies = [{"tmdb_id": m["id"], "title": m["title"], "poster_url": m["poster_url"]} for m in st.session_state.recently_viewed]
    
    # No fetch needed here, just render
    render_movies(recent_movies, cols=min(grid_cols, 4), key="recent", show_wl=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.recently_viewed = []
            st.toast("🗑️ Recent history cleared!")
            st.rerun()
    st.button("← Back", on_click=lambda: goto("home"))

# RANDOM PAGE
elif st.session_state.view == "random":
    st.markdown('<div class="section-title">🎲 Random Movie Picker</div>', unsafe_allow_html=True)
    st.markdown("### 🎯 Feeling lucky?")
    st.caption("Pick a random movie from your watchlist or popular movies")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎲 Pick a Random Movie!", use_container_width=True):
            pick_random_movie()
    if st.session_state.random_movie:
        movie = st.session_state.random_movie
        st.divider()
        
        # Add skeleton loading for movie details
        detail_key = f"details_{movie['id']}"
        if "prev_random_id" not in st.session_state:
            st.session_state.prev_random_id = None
            
        if st.session_state.prev_random_id != movie['id']:
            st.session_state.cached_data.pop(detail_key, None)
            st.session_state.loading_state.pop(detail_key, None)
            st.session_state.prev_random_id = movie['id']
            st.session_state.loading_state[detail_key] = True
            st.rerun()
            
        def fetch_detail():
            return api_get(f"/movie/id/{movie['id']}")
            
        data = load_data_with_skeleton(detail_key, fetch_detail, 1)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            show_poster(movie.get("poster_url"), border_radius="16px", fallback_size="4rem")
        with col2:
            st.markdown(f"## {movie.get('title', 'Unknown')}")
            if data and data.get("vote_average"):
                st.markdown(f"⭐ **{data['vote_average']:.1f}** / 10")
            if data and data.get("release_date"):
                st.caption(f"📅 {data.get('release_date', '-')}")
            if data and data.get("genres"):
                genres = " ".join([f"<span class='genre-tag'>{g['name']}</span>" for g in data['genres']])
                st.markdown(f"🎭 {genres}", unsafe_allow_html=True)
            st.divider()
            if data and data.get("overview"):
                st.markdown(data.get("overview", "No overview available."))
            st.divider()
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button("🎲 New Random", use_container_width=True):
                    pick_random_movie()
            with col_btn2:
                in_wl = movie["id"] in [x["id"] for x in st.session_state.watchlist]
                if st.button("✅ Remove" if in_wl else "➕ Add to Watchlist", use_container_width=True):
                    remove_watchlist(movie["id"]) if in_wl else add_watchlist(movie["id"], movie.get("title", ""), movie.get("poster_url"))
                    st.rerun()
            with col_btn3:
                # <--- FIXED ONE-CLICK: Using on_click callback here too for consistency
                st.button("▶ Open Details", use_container_width=True, on_click=lambda mid=movie["id"], title=movie.get("title", "Unknown"), poster=movie.get("poster_url"): (
                    add_recently_viewed(mid, title, poster),
                    goto("details", mid)
                ))
    else:
        st.info("🎯 Click 'Pick a Random Movie!' to get started!")
        st.caption("💡 If you have movies in your watchlist, it will pick from there first.")
    st.button("← Back to Home", on_click=lambda: goto("home"))

# DETAILS
elif st.session_state.view == "details":
    movie_id = st.session_state.selected_tmdb_id
    if not movie_id:
        goto("home")
        st.stop()
    
    # Load movie detail with skeleton
    detail_key = f"details_{movie_id}"
    if "prev_detail_id" not in st.session_state:
        st.session_state.prev_detail_id = None

    if st.session_state.prev_detail_id != movie_id:
        st.session_state.cached_data.pop(detail_key, None)
        st.session_state.loading_state.pop(detail_key, None)
        st.session_state.prev_detail_id = movie_id
        st.session_state.loading_state[detail_key] = True
        st.rerun()

    def fetch_current_detail():
        return api_get(f"/movie/id/{movie_id}")

    data = load_data_with_skeleton(detail_key, fetch_current_detail, 1)

    if data:
        col1, col2 = st.columns([1, 2])
        with col1:
            show_poster(data.get("poster_url") or data.get("poster_path"), border_radius="16px", fallback_size="4rem")
        with col2:
            st.markdown(f"## {data.get('title', '')}")
            if data.get("vote_average"):
                st.markdown(f"⭐ **{data['vote_average']:.1f}** / 10")
            st.caption(f"📅 {data.get('release_date', '-')}")
            if data.get("genres"):
                genres = " ".join([f"<span class='genre-tag'>{g['name']}</span>" for g in data['genres']])
                st.markdown(f"🎭 {genres}", unsafe_allow_html=True)
            st.divider()
            st.markdown(data.get("overview", "No overview available."))
            st.divider()
            in_wl = movie_id in [x["id"] for x in st.session_state.watchlist]
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ Remove" if in_wl else "➕ Add to Watchlist", use_container_width=True):
                    remove_watchlist(movie_id) if in_wl else add_watchlist(movie_id, data.get("title", ""), data.get("poster_url"))
                    st.rerun()
            with col_btn2:
                st.button("← Back", on_click=lambda: goto("home"), use_container_width=True)
        
        st.divider()
        st.markdown("### 🎯 You might also like")
        
        # Add skeleton loading for recommendations too!
        rec_key = f"recs_{movie_id}"
        if st.session_state.get("prev_rec_id", None) != movie_id:
            st.session_state.cached_data.pop(rec_key, None)
            st.session_state.loading_state.pop(rec_key, None)
            st.session_state.prev_rec_id = movie_id
            # We use a separate flag to not conflict with detail load
            st.session_state.loading_state[rec_key] = True
            st.rerun()

        def fetch_recs():
            return api_get("/movie/search", {"query": data.get("title", ""), "tfidf_top_n": 12, "genre_limit": 12})

        bundle = load_data_with_skeleton(rec_key, fetch_recs, min(grid_cols, 6))
        
        if bundle:
            recs = bundle.get("genre_recommendations") or bundle.get("tfidf_recommendations")
            if recs and len(recs) > 0:
                cards = []
                for rec in recs:
                    if bundle.get("genre_recommendations"):
                        cards.append({"tmdb_id": rec.get("tmdb_id"), "title": rec.get("title", "Unknown"), "poster_url": rec.get("poster_url"), "poster_path": rec.get("poster_path"), "vote_average": rec.get("vote_average")})
                    else:
                        tmdb = rec.get("tmdb", {})
                        if tmdb.get("tmdb_id"):
                            cards.append({"tmdb_id": tmdb.get("tmdb_id"), "title": tmdb.get("title") or rec.get("title", "Unknown"), "poster_url": tmdb.get("poster_url"), "poster_path": tmdb.get("poster_path"), "vote_average": tmdb.get("vote_average")})
                render_movies(cards, cols=min(grid_cols, 6), key="recs", show_wl=True) if cards else st.info("No recommendations available for this movie.")
            else:
                st.info("No recommendations available for this movie.")
        elif bundle is None and not st.session_state.loading_state.get(rec_key, False):
            st.info("Could not load recommendations. Please try again later.")
            
    elif data is None and not st.session_state.loading_state.get(detail_key, False):
        st.error("Movie not found.")
        st.button("← Back", on_click=lambda: goto("home"))
        st.stop()

# Footer
st.markdown(
    <div class="footer">
        "🎬" <span>Moovie
)
