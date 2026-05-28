import math
import os
import random
import sqlite3
import uuid
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "wordle_learning.db"


def find_asset_dir(dirname, required_file):
    candidates = [
        BASE_DIR / dirname,
        BASE_DIR,
        *BASE_DIR.glob(f"*/{dirname}"),
    ]
    for candidate in candidates:
        if (candidate / required_file).exists():
            return candidate
    return BASE_DIR / dirname

LEVELS = ["C1", "C2", "C3", "C4", "C5", "C6"]
WORD_LENGTHS = [4, 5, 6, 7]
LEVEL_TARGETS = {
    "C1": 80,
    "C2": 120,
    "C3": 160,
    "C4": 220,
    "C5": 280,
    "C6": 360,
}
REVIEW_INTERVALS = [1, 3, 7, 14, 30, 60]

WORD_BANK = [
    ("book", "書", "n.", "C1"),
    ("cold", "冷的", "adj.", "C1"),
    ("door", "門", "n.", "C1"),
    ("fish", "魚", "n.", "C1"),
    ("apple", "蘋果", "n.", "C1"),
    ("table", "桌子", "n.", "C1"),
    ("happy", "快樂的", "adj.", "C1"),
    ("water", "水", "n.", "C1"),
    ("study", "學習", "v.", "C1"),
    ("music", "音樂", "n.", "C1"),
    ("light", "光；輕的", "n./adj.", "C1"),
    ("green", "綠色的", "adj.", "C1"),
    ("bread", "麵包", "n.", "C1"),
    ("smile", "微笑", "v./n.", "C1"),
    ("animal", "動物", "n.", "C1"),
    ("family", "家庭", "n.", "C1"),
    ("orange", "橘子", "n.", "C1"),
    ("school", "學校", "n.", "C1"),
    ("morning", "早晨", "n.", "C1"),
    ("picture", "圖片", "n.", "C1"),
    ("student", "學生", "n.", "C1"),
    ("teacher", "老師", "n.", "C1"),
    ("area", "區域", "n.", "C2"),
    ("grow", "成長", "v.", "C2"),
    ("mind", "心智", "n.", "C2"),
    ("plan", "計畫", "n./v.", "C2"),
    ("travel", "旅行", "v./n.", "C2"),
    ("friend", "朋友", "n.", "C2"),
    ("forest", "森林", "n.", "C2"),
    ("market", "市場", "n.", "C2"),
    ("simple", "簡單的", "adj.", "C2"),
    ("answer", "回答", "v./n.", "C2"),
    ("future", "未來", "n.", "C2"),
    ("energy", "能量", "n.", "C2"),
    ("notice", "注意到；通知", "v./n.", "C2"),
    ("branch", "樹枝；分支", "n.", "C2"),
    ("ability", "能力", "n.", "C2"),
    ("believe", "相信", "v.", "C2"),
    ("central", "中心的", "adj.", "C2"),
    ("process", "過程", "n.", "C2"),
    ("bias", "偏見", "n.", "C3"),
    ("cope", "應付", "v.", "C3"),
    ("data", "資料", "n.", "C3"),
    ("vary", "變化", "v.", "C3"),
    ("adapt", "適應", "v.", "C3"),
    ("logic", "邏輯", "n.", "C3"),
    ("trend", "趨勢", "n.", "C3"),
    ("valid", "有效的", "adj.", "C3"),
    ("curious", "好奇的", "adj.", "C3"),
    ("balance", "平衡", "n./v.", "C3"),
    ("culture", "文化", "n.", "C3"),
    ("compare", "比較", "v.", "C3"),
    ("discuss", "討論", "v.", "C3"),
    ("protect", "保護", "v.", "C3"),
    ("visible", "可見的", "adj.", "C3"),
    ("journey", "旅程", "n.", "C3"),
    ("quality", "品質", "n.", "C3"),
    ("improve", "改善", "v.", "C3"),
    ("aid", "援助", "n./v.", "C4"),
    ("code", "代碼", "n.", "C4"),
    ("link", "連結", "n./v.", "C4"),
    ("role", "角色", "n.", "C4"),
    ("audit", "審核", "v./n.", "C4"),
    ("index", "索引；指標", "n.", "C4"),
    ("phase", "階段", "n.", "C4"),
    ("ratio", "比例", "n.", "C4"),
    ("accurate", "準確的", "adj.", "C4"),
    ("evidence", "證據", "n.", "C4"),
    ("identify", "辨識", "v.", "C4"),
    ("strategy", "策略", "n.", "C4"),
    ("resource", "資源", "n.", "C4"),
    ("solution", "解決方案", "n.", "C4"),
    ("priority", "優先事項", "n.", "C4"),
    ("analyze", "分析", "v.", "C4"),
    ("contrast", "對比", "v./n.", "C4"),
    ("frequent", "頻繁的", "adj.", "C4"),
    ("agenda", "議程", "n.", "C4"),
    ("derive", "取得；衍生", "v.", "C4"),
    ("insight", "洞察", "n.", "C4"),
    ("liberty", "自由", "n.", "C4"),
    ("cite", "引用", "v.", "C5"),
    ("norm", "規範", "n.", "C5"),
    ("scope", "範圍", "n.", "C5"),
    ("merit", "優點", "n.", "C5"),
    ("panel", "小組；面板", "n.", "C5"),
    ("rigor", "嚴謹", "n.", "C5"),
    ("ambiguous", "模稜兩可的", "adj.", "C5"),
    ("efficient", "有效率的", "adj.", "C5"),
    ("substance", "物質；實質", "n.", "C5"),
    ("influence", "影響", "n./v.", "C5"),
    ("evaluate", "評估", "v.", "C5"),
    ("maintain", "維持", "v.", "C5"),
    ("significant", "重要的", "adj.", "C5"),
    ("interpret", "詮釋", "v.", "C5"),
    ("objective", "客觀的；目標", "adj./n.", "C5"),
    ("phenomenon", "現象", "n.", "C5"),
    ("domain", "領域", "n.", "C5"),
    ("ethical", "合乎倫理的", "adj.", "C5"),
    ("intrude", "侵入", "v.", "C5"),
    ("utility", "效用", "n.", "C5"),
    ("axis", "軸線", "n.", "C6"),
    ("flux", "流動；變動", "n.", "C6"),
    ("mode", "模式", "n.", "C6"),
    ("rare", "稀有的", "adj.", "C6"),
    ("hypothesis", "假設", "n.", "C6"),
    ("synthesize", "綜合", "v.", "C6"),
    ("resilience", "韌性", "n.", "C6"),
    ("meticulous", "一絲不苟的", "adj.", "C6"),
    ("paradigm", "典範", "n.", "C6"),
    ("equivalent", "等同的", "adj.", "C6"),
    ("constraint", "限制", "n.", "C6"),
    ("implication", "含意；影響", "n.", "C6"),
    ("preliminary", "初步的", "adj.", "C6"),
    ("comprehensive", "全面的", "adj.", "C6"),
    ("axiom", "公理", "n.", "C6"),
    ("latent", "潛在的", "adj.", "C6"),
    ("nuance", "細微差別", "n.", "C6"),
    ("quantum", "量子的", "adj.", "C6"),
]

VALID_GUESS_WORDS = {
    word for word, _meaning, _pos, _level in WORD_BANK
} | {
    "able", "acid", "aged", "also", "area", "army", "away", "baby", "back", "ball", "band", "bank",
    "base", "bath", "bear", "beat", "been", "beer", "bell", "belt", "best", "bill", "bird", "blow",
    "blue", "boat", "body", "bond", "bone", "born", "boss", "both", "bowl", "bulk", "burn", "busy",
    "call", "calm", "came", "camp", "card", "care", "case", "cash", "cast", "cell", "chat", "chip",
    "city", "club", "coal", "coat", "code", "come", "cook", "cool", "cope", "copy", "core", "cost",
    "crew", "crop", "dark", "data", "date", "dawn", "days", "dead", "deal", "dear", "debt", "deep",
    "deny", "desk", "dial", "diet", "disc", "disk", "does", "done", "dose", "down", "draw", "drew",
    "drop", "drug", "dual", "duke", "dust", "duty", "each", "earn", "ease", "east", "easy", "edge",
    "else", "even", "ever", "evil", "exit", "face", "fact", "fail", "fair", "fall", "farm", "fast",
    "fate", "fear", "feed", "feel", "feet", "fell", "felt", "file", "fill", "film", "find", "fine",
    "fire", "firm", "flat", "flow", "fold", "food", "foot", "form", "fort", "free", "from", "fuel",
    "full", "fund", "gain", "game", "gate", "gave", "gear", "gene", "gift", "girl", "give", "glad",
    "goal", "goes", "gold", "golf", "gone", "good", "gray", "grew", "grid", "grow", "gulf", "hair",
    "half", "hall", "hand", "hang", "hard", "harm", "hate", "have", "head", "hear", "heat", "held",
    "help", "here", "hero", "high", "hill", "hire", "hold", "hole", "holy", "home", "hope", "host",
    "hour", "huge", "hung", "hunt", "hurt", "idea", "inch", "into", "iron", "item", "jack", "join",
    "jump", "jury", "just", "keen", "keep", "kept", "kick", "kill", "kind", "king", "knee", "knew",
    "know", "lack", "lady", "laid", "lake", "land", "lane", "last", "late", "lead", "left", "less",
    "life", "lift", "like", "line", "link", "list", "live", "load", "loan", "lock", "logo", "long",
    "look", "lord", "lose", "loss", "lost", "love", "luck", "made", "mail", "main", "make", "male",
    "many", "mark", "mass", "meal", "mean", "meat", "meet", "menu", "mere", "mild", "mile", "milk",
    "mill", "mind", "mine", "miss", "mode", "mood", "moon", "more", "most", "move", "much", "must",
    "name", "navy", "near", "neck", "need", "news", "next", "nice", "nine", "none", "nose", "note",
    "okay", "once", "only", "onto", "open", "oral", "over", "pace", "pack", "page", "paid", "pain",
    "pair", "pale", "palm", "park", "part", "pass", "past", "path", "peak", "pick", "pink", "pipe",
    "plan", "play", "plot", "plug", "plus", "poll", "pool", "poor", "port", "post", "pull", "pure",
    "push", "race", "rail", "rain", "rank", "rare", "rate", "read", "real", "rear", "rely", "rent",
    "rest", "rice", "rich", "ride", "ring", "rise", "risk", "road", "rock", "role", "roll", "roof",
    "room", "root", "rose", "rule", "rush", "safe", "said", "sake", "sale", "salt", "same", "sand",
    "save", "seat", "seed", "seek", "seem", "seen", "self", "sell", "send", "sent", "ship", "shop",
    "shot", "show", "shut", "sick", "side", "sign", "site", "size", "skin", "slip", "slow", "snow",
    "soft", "soil", "sold", "sole", "some", "song", "soon", "sort", "soul", "spot", "star", "stay",
    "step", "stop", "such", "suit", "sure", "take", "tale", "talk", "tall", "tank", "tape", "task",
    "team", "tear", "tell", "tend", "term", "test", "text", "than", "that", "them", "then", "they",
    "thin", "this", "thus", "tide", "tied", "tile", "time", "tiny", "told", "tone", "took", "tool",
    "tour", "town", "tree", "trip", "true", "tube", "tune", "turn", "twin", "type", "unit", "upon",
    "used", "user", "vary", "vast", "very", "vice", "view", "vote", "wage", "wait", "wake", "walk",
    "wall", "want", "ward", "warm", "wash", "wave", "ways", "weak", "wear", "week", "well", "went",
    "were", "west", "what", "when", "whom", "wide", "wife", "wild", "will", "wind", "wine", "wing",
    "wire", "wise", "wish", "with", "wood", "word", "wore", "work", "yard", "yeah", "year", "your",
    "youth",
    "about", "above", "abuse", "actor", "acute", "admit", "adopt", "adult", "after", "again", "agent",
    "agree", "ahead", "alarm", "album", "alert", "alike", "alive", "allow", "alone", "along", "alter",
    "among", "anger", "angle", "angry", "apart", "apply", "arena", "argue", "arise", "array", "aside",
    "asset", "audio", "avoid", "award", "aware", "badly", "basic", "basis", "beach", "began", "begin",
    "begun", "being", "below", "bench", "birth", "black", "blame", "blind", "block", "blood", "board",
    "brain", "brand", "brave", "break", "breed", "brief", "bring", "broad", "broke", "brown", "build",
    "built", "buyer", "cable", "carry", "catch", "cause", "chain", "chair", "chart", "chase", "cheap",
    "check", "chest", "chief", "child", "china", "chose", "civil", "claim", "class", "clean", "clear",
    "click", "clock", "close", "coach", "coast", "could", "count", "court", "cover", "craft", "crash",
    "cream", "crime", "cross", "crowd", "crown", "cycle", "daily", "dance", "dealt", "death", "delay",
    "depth", "doing", "doubt", "dozen", "draft", "drama", "drawn", "dream", "dress", "drink", "drive",
    "drove", "dying", "eager", "early", "earth", "eight", "elite", "empty", "enemy", "enjoy", "enter",
    "entry", "equal", "error", "event", "every", "exact", "exist", "extra", "faith", "false", "fault",
    "fiber", "field", "fifth", "fifty", "fight", "final", "first", "fixed", "flash", "fleet", "floor",
    "fluid", "focus", "force", "forth", "forty", "forum", "found", "frame", "fresh", "front", "fruit",
    "fully", "funny", "giant", "given", "glass", "globe", "going", "grace", "grade", "grand", "grant",
    "grass", "great", "green", "gross", "group", "grown", "guard", "guess", "guest", "guide", "happy",
    "harry", "heart", "heavy", "hence", "henry", "horse", "hotel", "house", "human", "ideal", "image",
    "index", "inner", "input", "issue", "japan", "joint", "judge", "known", "label", "large", "laser",
    "later", "laugh", "layer", "learn", "lease", "least", "leave", "legal", "level", "light", "limit",
    "local", "logic", "loose", "lower", "lucky", "lunch", "lying", "magic", "major", "maker", "march",
    "match", "maybe", "mayor", "meant", "media", "metal", "might", "minor", "minus", "mixed", "model",
    "money", "month", "moral", "motor", "mount", "mouse", "mouth", "movie", "music", "needs", "never",
    "newly", "night", "noise", "north", "novel", "nurse", "occur", "ocean", "offer", "often", "order",
    "other", "ought", "paint", "panel", "paper", "party", "peace", "peter", "phase", "phone", "photo",
    "piece", "pilot", "pitch", "place", "plain", "plane", "plant", "plate", "point", "pound", "power",
    "press", "price", "pride", "prime", "print", "prior", "prize", "proof", "proud", "prove", "queen",
    "quick", "quiet", "quite", "radio", "raise", "range", "rapid", "ratio", "reach", "ready", "refer",
    "right", "rival", "river", "roman", "rough", "round", "route", "royal", "rural", "scale", "scene",
    "scope", "score", "sense", "serve", "seven", "shall", "shape", "share", "sharp", "sheet", "shelf",
    "shell", "shift", "shirt", "shock", "shoot", "short", "shown", "sight", "since", "sixth", "sixty",
    "skill", "sleep", "small", "smart", "smile", "smith", "solid", "solve", "sorry", "sound", "south",
    "space", "spare", "speak", "speed", "spend", "spent", "split", "spoke", "sport", "staff", "stage",
    "stake", "stand", "start", "state", "steam", "steel", "stick", "still", "stock", "stone", "stood",
    "store", "storm", "story", "strip", "stuck", "style", "sugar", "suite", "super", "sweet", "table",
    "taken", "taste", "teach", "teeth", "terry", "texas", "thank", "theme", "there", "thick", "thing",
    "think", "third", "those", "three", "threw", "throw", "tight", "times", "tired", "title", "today",
    "topic", "total", "touch", "tough", "tower", "track", "trade", "train", "treat", "trend", "trial",
    "tried", "tries", "truck", "truly", "trust", "truth", "twice", "under", "union", "unity", "until",
    "upper", "upset", "urban", "usage", "usual", "valid", "value", "video", "virus", "visit", "vital",
    "voice", "waste", "watch", "water", "wheel", "where", "which", "while", "white", "whole", "whose",
    "woman", "world", "worry", "worse", "worst", "worth", "would", "write", "wrong", "wrote", "yield",
    "young",
    "ability", "absent", "accept", "access", "across", "acting", "action", "active", "actual", "advice",
    "advise", "affect", "afford", "afraid", "agency", "agenda", "almost", "always", "amount", "animal",
    "annual", "answer", "anyone", "appeal", "appear", "around", "arrive", "artist", "aspect", "assess",
    "assist", "assume", "attack", "attend", "august", "author", "backup", "barely", "battle", "beauty",
    "become", "before", "belief", "belong", "better", "beyond", "border", "bottle", "bottom", "bought",
    "branch", "breath", "bridge", "bright", "broken", "budget", "burden", "bureau", "button", "camera",
    "cancer", "cannot", "carbon", "career", "castle", "casual", "caught", "center", "chance", "change",
    "charge", "choice", "choose", "chosen", "church", "circle", "client", "closed", "closer", "coffee",
    "column", "combat", "coming", "common", "comply", "copper", "corner", "costly", "county", "couple",
    "course", "covers", "create", "credit", "crisis", "custom", "damage", "danger", "dealer", "debate",
    "decade", "decide", "defeat", "defend", "define", "degree", "demand", "depend", "deputy", "desert",
    "design", "desire", "detail", "detect", "device", "differ", "dinner", "direct", "doctor", "dollar",
    "domain", "double", "driven", "driver", "during", "easily", "eating", "editor", "effect", "effort",
    "either", "eleven", "emerge", "empire", "employ", "enable", "ending", "energy", "engage", "engine",
    "enough", "ensure", "entire", "entity", "equity", "escape", "estate", "ethical", "except", "excess",
    "expand", "expect", "expert", "export", "extend", "extent", "fabric", "facing", "factor", "failed",
    "fairly", "fallen", "family", "famous", "father", "fellow", "female", "figure", "filing", "finger",
    "finish", "fiscal", "flight", "follow", "forced", "forest", "forget", "formal", "format", "former",
    "foster", "fought", "fourth", "friend", "future", "garden", "gather", "gender", "global", "golden",
    "ground", "growth", "guilty", "handed", "handle", "happen", "hardly", "headed", "health", "height",
    "hidden", "holder", "honest", "impact", "import", "income", "indeed", "injury", "inside", "intend",
    "intent", "invest", "island", "itself", "jacket", "junior", "killed", "labour", "latest", "latter",
    "launch", "lawyer", "leader", "league", "legacy", "length", "lesson", "letter", "lights", "likely",
    "linked", "liquid", "listen", "little", "living", "losing", "mainly", "manage", "manner", "manual",
    "margin", "market", "master", "matter", "mature", "medium", "memory", "mental", "merely", "method",
    "middle", "minute", "mirror", "mobile", "modern", "modest", "mostly", "mother", "motion", "murder",
    "museum", "mutual", "myself", "narrow", "nation", "native", "nature", "nearby", "nearly", "nights",
    "nobody", "normal", "notice", "notion", "number", "object", "obtain", "office", "online", "option",
    "orange", "origin", "output", "oxford", "packed", "palace", "parent", "partly", "patent", "people",
    "period", "permit", "person", "phrase", "picked", "planet", "player", "please", "plenty", "pocket",
    "police", "policy", "prefer", "pretty", "prince", "prison", "profit", "proper", "proven", "public",
    "pursue", "raised", "random", "rarely", "rather", "rating", "reader", "really", "reason", "recall",
    "recent", "record", "reduce", "reform", "regard", "regime", "region", "relate", "relief", "remain",
    "remote", "remove", "repair", "repeat", "replay", "report", "rescue", "resort", "result", "retail",
    "retain", "return", "reveal", "review", "reward", "rising", "robust", "ruling", "safety", "salary",
    "sample", "saving", "saying", "scheme", "school", "screen", "search", "season", "second", "secret",
    "sector", "secure", "seeing", "select", "seller", "senior", "series", "server", "settle", "severe",
    "sexual", "should", "signal", "signed", "silent", "silver", "simple", "simply", "single", "sister",
    "slight", "smooth", "social", "solely", "sought", "source", "soviet", "speech", "spirit", "spoken",
    "spread", "spring", "square", "stable", "status", "steady", "stolen", "strain", "stream", "street",
    "stress", "strict", "strike", "string", "strong", "struck", "studio", "submit", "sudden", "suffer",
    "summer", "summit", "supply", "surely", "survey", "switch", "symbol", "system", "taking", "talent",
    "target", "taught", "tenant", "tender", "tennis", "thanks", "theory", "thirty", "though", "threat",
    "thrown", "ticket", "timely", "timing", "tissue", "toward", "travel", "treaty", "trying", "twelve",
    "twenty", "unable", "unique", "united", "unless", "unlike", "update", "useful", "valley", "varied",
    "vendor", "versus", "victim", "vision", "visual", "volume", "walker", "wealth", "weekly", "weight",
    "window", "winner", "winter", "within", "wonder", "worker", "wright", "yellow",
    "absence", "academy", "account", "accused", "achieve", "acquire", "address", "advance", "adverse",
    "advised", "adviser", "against", "airline", "airport", "alcohol", "already", "analyst", "ancient",
    "another", "anxiety", "anxious", "anybody", "applied", "arrange", "arrival", "article", "assault",
    "attempt", "attract", "auction", "average", "backing", "balance", "banking", "barrier", "battery",
    "bearing", "beating", "because", "bedroom", "believe", "beneath", "benefit", "besides", "between",
    "billion", "binding", "brother", "brought", "burning", "cabinet", "caliber", "calling", "capable",
    "capital", "captain", "caption", "capture", "careful", "carrier", "caution", "ceiling", "central",
    "centric", "century", "certain", "chamber", "channel", "chapter", "charity", "charlie", "charter",
    "checked", "chicken", "chronic", "circuit", "classes", "classic", "climate", "closing", "closure",
    "clothes", "collect", "college", "combine", "comfort", "command", "comment", "company", "compare",
    "complex", "concept", "concern", "concert", "conduct", "confirm", "connect", "consent", "consist",
    "contact", "contain", "content", "contest", "context", "control", "convert", "correct", "council",
    "counsel", "counter", "country", "crucial", "culture", "current", "cutting", "dealing", "decided",
    "decline", "default", "defence", "deficit", "deliver", "density", "deposit", "desktop", "despite",
    "destroy", "develop", "devoted", "diamond", "digital", "discuss", "disease", "display", "dispute",
    "distant", "diverse", "divided", "drawing", "driving", "dynamic", "eastern", "economy", "edition",
    "elderly", "element", "engaged", "enhance", "essence", "evening", "evident", "exactly", "examine",
    "example", "excited", "exclude", "exhibit", "expense", "explain", "explore", "express", "extreme",
    "factory", "faculty", "failing", "failure", "fashion", "feature", "federal", "feeling", "fiction",
    "fifteen", "filling", "finance", "finding", "fishing", "fitness", "foreign", "forever", "formula",
    "fortune", "forward", "founder", "freedom", "further", "gallery", "gateway", "general", "genetic",
    "genuine", "greater", "hanging", "heading", "healthy", "hearing", "heavily", "helpful", "herself",
    "highway", "himself", "history", "holding", "holiday", "housing", "however", "hundred", "husband",
    "illegal", "illness", "imagine", "imaging", "improve", "include", "initial", "inquiry", "insight",
    "install", "instant", "instead", "intense", "interim", "involve", "jointly", "journal", "journey",
    "justice", "justify", "keeping", "killing", "kingdom", "kitchen", "knowing", "landing", "largely",
    "lasting", "leading", "learned", "leisure", "liberal", "liberty", "library", "license", "limited",
    "listing", "logical", "machine", "manager", "married", "massive", "maximum", "meaning", "measure",
    "medical", "meeting", "mention", "message", "million", "mineral", "minimal", "minimum", "missing",
    "mission", "mistake", "mixture", "monitor", "monthly", "morning", "musical", "mystery", "natural",
    "neither", "nervous", "network", "neutral", "notable", "nothing", "nowhere", "nuclear", "nursing",
    "obvious", "offense", "officer", "ongoing", "opening", "operate", "opinion", "optical", "organic",
    "outcome", "outdoor", "outlook", "outside", "overall", "package", "painted", "parking", "partial",
    "partner", "passage", "passing", "passion", "passive", "patient", "pattern", "payable", "payment",
    "penalty", "pending", "pension", "percent", "perfect", "perform", "perhaps", "phoenix", "picking",
    "picture", "pioneer", "plastic", "pointed", "popular", "portion", "poverty", "precise", "predict",
    "premier", "premium", "prepare", "present", "prevent", "primary", "printer", "privacy", "private",
    "problem", "proceed", "process", "produce", "product", "profile", "program", "project", "promise",
    "promote", "protect", "protein", "protest", "provide", "publish", "purpose", "pushing", "qualify",
    "quality", "quarter", "radical", "railway", "readily", "reading", "reality", "realize", "receipt",
    "receive", "recover", "reflect", "regular", "related", "release", "remains", "removal", "removed",
    "replace", "request", "require", "reserve", "resolve", "respect", "respond", "restore", "retired",
    "revenue", "reverse", "rollout", "routine", "running", "satisfy", "science", "section", "segment",
    "serious", "service", "serving", "session", "setting", "seventh", "several", "shortly", "showing",
    "silence", "silicon", "similar", "sitting", "sixteen", "skilled", "smoking", "society", "somehow",
    "speaker", "special", "species", "sponsor", "station", "storage", "strange", "stretch", "student",
    "studied", "subject", "succeed", "success", "suggest", "summary", "support", "suppose", "supreme",
    "surface", "surgery", "surplus", "survive", "teacher", "telecom", "telling", "tension", "theater",
    "therapy", "thereby", "thought", "through", "tonight", "totally", "touched", "towards", "traffic",
    "trouble", "turning", "typical", "uniform", "unknown", "unusual", "upgrade", "upscale", "utility",
    "variety", "various", "vehicle", "venture", "version", "veteran", "victory", "viewing", "village",
    "violent", "virtual", "visible", "waiting", "walking", "wanting", "warning", "warrant", "wearing",
    "weather", "webcast", "website", "wedding", "weekend", "welcome", "welfare", "western", "whereas",
    "whereby", "whether", "willing", "winning", "without", "witness", "working", "writing",
}


app = Flask(
    __name__,
    template_folder=str(find_asset_dir("templates", "auth.html")),
    static_folder=str(find_asset_dir("static", "style.css")),
)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-wordle-learning-secret")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            user_id TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            user_id INTEGER PRIMARY KEY,
            difficulty TEXT NOT NULL,
            word_length INTEGER NOT NULL DEFAULT 5,
            exam_date TEXT NOT NULL,
            daily_target INTEGER NOT NULL,
            initialized_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            meaning TEXT NOT NULL,
            part_of_speech TEXT NOT NULL,
            level TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            word_id INTEGER NOT NULL,
            level TEXT NOT NULL,
            success INTEGER NOT NULL,
            attempts INTEGER NOT NULL,
            source TEXT NOT NULL,
            played_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (word_id) REFERENCES words(id)
        );

        CREATE TABLE IF NOT EXISTS mistakes (
            user_id INTEGER NOT NULL,
            word_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (user_id, word_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (word_id) REFERENCES words(id)
        );

        CREATE TABLE IF NOT EXISTS word_progress (
            user_id INTEGER NOT NULL,
            word_id INTEGER NOT NULL,
            times_seen INTEGER NOT NULL DEFAULT 0,
            streak INTEGER NOT NULL DEFAULT 0,
            interval_days INTEGER NOT NULL DEFAULT 0,
            next_review TEXT,
            last_result INTEGER,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, word_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (word_id) REFERENCES words(id)
        );

        CREATE TABLE IF NOT EXISTS daily_progress (
            user_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            consumed_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, day),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    db.executemany(
        """
        INSERT OR IGNORE INTO words (word, meaning, part_of_speech, level)
        VALUES (?, ?, ?, ?)
        """,
        WORD_BANK,
    )
    columns = [row[1] for row in db.execute("PRAGMA table_info(settings)").fetchall()]
    if "word_length" not in columns:
        db.execute("ALTER TABLE settings ADD COLUMN word_length INTEGER NOT NULL DEFAULT 5")
    db.commit()
    db.close()


def current_user():
    user_pk = session.get("user_pk")
    if not user_pk:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_pk,)).fetchone()


def require_user():
    user = current_user()
    if not user:
        return redirect(url_for("auth"))
    return None


def user_settings(user_pk):
    return get_db().execute("SELECT * FROM settings WHERE user_id = ?", (user_pk,)).fetchone()


def days_until_exam(exam_date_text):
    exam_day = datetime.strptime(exam_date_text, "%Y-%m-%d").date()
    return max((exam_day - date.today()).days, 1)


def calculate_daily_target(level, exam_date_text):
    remaining_days = days_until_exam(exam_date_text)
    target_total = LEVEL_TARGETS[level]
    return max(1, min(25, math.ceil(target_total / remaining_days)))


def level_index(level):
    return LEVELS.index(level)


def level_accuracy(user_pk, level):
    db = get_db()
    history_count = db.execute(
        """
        SELECT COUNT(DISTINCT word_id) AS c
        FROM history
        WHERE user_id = ? AND level = ?
        """,
        (user_pk, level),
    ).fetchone()["c"]
    if history_count == 0:
        return None, 0, 0
    mistake_count = db.execute(
        """
        SELECT COUNT(*) AS c
        FROM mistakes m
        JOIN words w ON w.id = m.word_id
        WHERE m.user_id = ? AND w.level = ?
        """,
        (user_pk, level),
    ).fetchone()["c"]
    return max(0, 1 - (mistake_count / history_count)), history_count, mistake_count


def choose_adaptive_level(user_pk, base_level):
    accuracy, total, _mistakes = level_accuracy(user_pk, base_level)
    if total < 10 or accuracy is None:
        return base_level
    idx = level_index(base_level)
    if accuracy > 0.85 and idx < len(LEVELS) - 1:
        return LEVELS[idx + 1] if random.random() < 0.25 else base_level
    if accuracy < 0.60 and idx > 0:
        return LEVELS[idx - 1] if random.random() < 0.30 else base_level
    return base_level


def get_due_review_word(user_pk, word_length):
    row = get_db().execute(
        """
        SELECT w.*
        FROM word_progress p
        JOIN words w ON w.id = p.word_id
        WHERE p.user_id = ?
          AND LENGTH(w.word) = ?
          AND p.next_review IS NOT NULL
          AND p.next_review <= ?
        ORDER BY p.next_review ASC, RANDOM()
        LIMIT 1
        """,
        (user_pk, word_length, date.today().isoformat()),
    ).fetchone()
    return row


def get_mistake_word(user_pk, word_length):
    return get_db().execute(
        """
        SELECT w.*
        FROM mistakes m
        JOIN words w ON w.id = m.word_id
        WHERE m.user_id = ? AND LENGTH(w.word) = ?
        ORDER BY RANDOM()
        LIMIT 1
        """,
        (user_pk, word_length),
    ).fetchone()


def choose_word(user_pk, base_level, word_length):
    accuracy, total, _mistakes = level_accuracy(user_pk, base_level)
    if total >= 10 and accuracy is not None and accuracy < 0.60 and random.random() < 0.35:
        mistake = get_mistake_word(user_pk, word_length)
        if mistake:
            return mistake

    due = get_due_review_word(user_pk, word_length)
    if due:
        return due

    selected_level = choose_adaptive_level(user_pk, base_level)
    db = get_db()
    new_word = db.execute(
        """
        SELECT w.*
        FROM words w
        WHERE w.level = ?
          AND LENGTH(w.word) = ?
          AND NOT EXISTS (
              SELECT 1 FROM history h
              WHERE h.user_id = ? AND h.word_id = w.id
          )
        ORDER BY RANDOM()
        LIMIT 1
        """,
        (selected_level, word_length, user_pk),
    ).fetchone()
    if new_word:
        return new_word

    same_level_word = db.execute(
        """
        SELECT w.*
        FROM words w
        WHERE w.level = ? AND LENGTH(w.word) = ?
        ORDER BY RANDOM()
        LIMIT 1
        """,
        (selected_level, word_length),
    ).fetchone()
    if same_level_word:
        return same_level_word

    return db.execute(
        """
        SELECT w.*
        FROM words w
        WHERE LENGTH(w.word) = ?
        ORDER BY RANDOM()
        LIMIT 1
        """,
        (word_length,),
    ).fetchone()


def score_guess(answer, guess):
    answer = answer.lower()
    guess = guess.lower()
    result = ["absent"] * len(answer)
    remaining = Counter()

    for idx, letter in enumerate(answer):
        if guess[idx] == letter:
            result[idx] = "correct"
        else:
            remaining[letter] += 1

    for idx, letter in enumerate(guess):
        if result[idx] == "correct":
            continue
        if remaining[letter] > 0:
            result[idx] = "present"
            remaining[letter] -= 1

    return result


def is_valid_guess(guess):
    return guess.lower() in VALID_GUESS_WORDS


def keyboard_rows(guesses):
    priority = {"unused": 0, "absent": 1, "present": 2, "correct": 3}
    states = {chr(code): "unused" for code in range(ord("a"), ord("z") + 1)}
    for guess in guesses:
        for letter, mark in zip(guess["text"], guess["marks"]):
            letter = letter.lower()
            if priority[mark] > priority[states[letter]]:
                states[letter] = mark

    return [
        [{"letter": letter, "state": states[letter.lower()]} for letter in row]
        for row in ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    ]


def add_history(user_pk, word_id, level, success, attempts, source):
    get_db().execute(
        """
        INSERT INTO history (user_id, word_id, level, success, attempts, source, played_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_pk, word_id, level, int(success), attempts, source, datetime.now().isoformat(timespec="seconds")),
    )


def add_mistake(user_pk, word_id):
    get_db().execute(
        """
        INSERT OR IGNORE INTO mistakes (user_id, word_id, created_at)
        VALUES (?, ?, ?)
        """,
        (user_pk, word_id, datetime.now().isoformat(timespec="seconds")),
    )


def remove_mistake(user_pk, word_id):
    get_db().execute("DELETE FROM mistakes WHERE user_id = ? AND word_id = ?", (user_pk, word_id))


def update_spaced_repetition(user_pk, word_id, success):
    db = get_db()
    progress = db.execute(
        "SELECT * FROM word_progress WHERE user_id = ? AND word_id = ?",
        (user_pk, word_id),
    ).fetchone()
    today = date.today()
    if progress:
        times_seen = progress["times_seen"] + 1
        if success:
            streak = progress["streak"] + 1
            current_interval = progress["interval_days"] or 1
            interval = next((v for v in REVIEW_INTERVALS if v > current_interval), REVIEW_INTERVALS[-1])
        else:
            streak = 0
            interval = 1
        next_review = (today + timedelta(days=interval)).isoformat()
        db.execute(
            """
            UPDATE word_progress
            SET times_seen = ?, streak = ?, interval_days = ?, next_review = ?,
                last_result = ?, updated_at = ?
            WHERE user_id = ? AND word_id = ?
            """,
            (
                times_seen,
                streak,
                interval,
                next_review,
                int(success),
                datetime.now().isoformat(timespec="seconds"),
                user_pk,
                word_id,
            ),
        )
    else:
        interval = 1
        next_review = (today + timedelta(days=interval)).isoformat()
        db.execute(
            """
            INSERT INTO word_progress
                (user_id, word_id, times_seen, streak, interval_days, next_review, last_result, updated_at)
            VALUES (?, ?, 1, ?, ?, ?, ?, ?)
            """,
            (
                user_pk,
                word_id,
                1 if success else 0,
                interval,
                next_review,
                int(success),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def increment_daily_progress(user_pk):
    today = date.today().isoformat()
    db = get_db()
    db.execute(
        """
        INSERT INTO daily_progress (user_id, day, consumed_count)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, day) DO UPDATE SET consumed_count = consumed_count + 1
        """,
        (user_pk, today),
    )


def finalize_wordle(success):
    user = current_user()
    word_id = session.get("current_word_id")
    if not user or not word_id:
        return
    db = get_db()
    word = db.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
    attempts = len(session.get("guesses", []))
    add_history(user["id"], word["id"], word["level"], success, attempts, "wordle")
    update_spaced_repetition(user["id"], word["id"], success)
    if not success:
        add_mistake(user["id"], word["id"])
    increment_daily_progress(user["id"])
    db.commit()
    session.pop("current_word_id", None)
    session.pop("guesses", None)
    session.pop("awaiting_revival", None)
    session.pop("revival_word_id", None)
    session.pop("revival_options", None)
    session.pop("max_attempts", None)
    session.pop("revived", None)
    session["last_result"] = "success" if success else "failed"


def today_status(user_pk):
    settings = user_settings(user_pk)
    today = date.today().isoformat()
    completed = get_db().execute(
        "SELECT consumed_count FROM daily_progress WHERE user_id = ? AND day = ?",
        (user_pk, today),
    ).fetchone()
    completed_count = completed["consumed_count"] if completed else 0
    daily_target = settings["daily_target"] if settings else 1
    due_count = get_db().execute(
        """
        SELECT COUNT(*) AS c
        FROM word_progress
        WHERE user_id = ? AND next_review IS NOT NULL AND next_review <= ?
        """,
        (user_pk, today),
    ).fetchone()["c"]
    remaining = max(daily_target - completed_count, 0)
    percent = min(100, round((completed_count / daily_target) * 100)) if daily_target else 0
    return {
        "completed": completed_count,
        "target": daily_target,
        "remaining": remaining,
        "due_count": due_count,
        "percent": percent,
    }


def build_mcq_options(correct_word):
    db = get_db()
    distractors = db.execute(
        """
        SELECT meaning FROM words
        WHERE id != ?
        ORDER BY RANDOM()
        LIMIT 3
        """,
        (correct_word["id"],),
    ).fetchall()
    options = [correct_word["meaning"]] + [row["meaning"] for row in distractors]
    random.shuffle(options)
    return options


def prepare_revival(user_pk):
    db = get_db()
    revival_word = db.execute(
        """
        SELECT DISTINCT w.*
        FROM history h
        JOIN words w ON w.id = h.word_id
        WHERE h.user_id = ? AND h.success = 1 AND w.id != ?
        ORDER BY RANDOM()
        LIMIT 1
        """,
        (user_pk, session.get("current_word_id")),
    ).fetchone()
    if not revival_word:
        return False
    session["awaiting_revival"] = True
    session["revival_word_id"] = revival_word["id"]
    session["revival_options"] = build_mcq_options(revival_word)
    return True


@app.context_processor
def inject_globals():
    user = current_user()
    return {
        "current_user": user,
        "levels": LEVELS,
    }


@app.route("/")
def index():
    user = current_user()
    if not user:
        return redirect(url_for("auth"))
    if not user_settings(user["id"]):
        return redirect(url_for("setup"))
    return redirect(url_for("game"))


@app.route("/auth")
def auth():
    if current_user():
        return redirect(url_for("index"))
    return render_template("auth.html")


@app.get("/api/check-username")
def check_username():
    username = request.args.get("username", "").strip()
    if len(username) < 2:
        return jsonify({"available": False, "message": "至少 2 個字"})
    exists = get_db().execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
    if exists:
        return jsonify({"available": False, "message": "已被使用"})
    return jsonify({"available": True, "message": "可以使用"})


@app.post("/register")
def register():
    username = request.form.get("username", "").strip()
    if len(username) < 2:
        flash("使用者名稱至少需要 2 個字。", "error")
        return redirect(url_for("auth"))
    db = get_db()
    try:
        user_id = str(uuid.uuid4())
        cursor = db.execute(
            "INSERT INTO users (username, user_id, created_at) VALUES (?, ?, ?)",
            (username, user_id, datetime.now().isoformat(timespec="seconds")),
        )
        db.commit()
        session["user_pk"] = cursor.lastrowid
        flash("註冊成功，系統已替你建立 User_ID。", "success")
        return redirect(url_for("setup"))
    except sqlite3.IntegrityError:
        flash("這個使用者名稱已經被使用，請換一個。", "error")
        return redirect(url_for("auth"))


@app.post("/login")
def login():
    identifier = request.form.get("identifier", "").strip()
    user = get_db().execute(
        "SELECT * FROM users WHERE username = ? OR user_id = ?",
        (identifier, identifier),
    ).fetchone()
    if not user:
        flash("找不到這個帳號名稱或 User_ID。", "error")
        return redirect(url_for("auth"))
    session["user_pk"] = user["id"]
    flash("登入成功，學習進度已同步。", "success")
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    flash("你已登出。", "success")
    return redirect(url_for("auth"))


@app.route("/setup", methods=["GET", "POST"])
def setup():
    guard = require_user()
    if guard:
        return guard
    user = current_user()
    existing = user_settings(user["id"])
    if request.method == "POST":
        difficulty = request.form.get("difficulty", "C1")
        word_length = int(request.form.get("word_length", "5"))
        exam_date = request.form.get("exam_date", "")
        if difficulty not in LEVELS:
            flash("請選擇有效的難度。", "error")
            return redirect(url_for("setup"))
        if word_length not in WORD_LENGTHS:
            flash("請選擇有效的單字長度。", "error")
            return redirect(url_for("setup"))
        try:
            parsed_exam_date = datetime.strptime(exam_date, "%Y-%m-%d").date()
        except ValueError:
            flash("請輸入有效的考試日期。", "error")
            return redirect(url_for("setup"))
        if parsed_exam_date < date.today():
            flash("考試日期不能早於今天。", "error")
            return redirect(url_for("setup"))

        daily_target = calculate_daily_target(difficulty, exam_date)
        db = get_db()
        db.execute(
            """
            INSERT INTO settings (user_id, difficulty, word_length, exam_date, daily_target, initialized_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                difficulty = excluded.difficulty,
                word_length = excluded.word_length,
                exam_date = excluded.exam_date,
                daily_target = excluded.daily_target,
                initialized_at = excluded.initialized_at
            """,
            (
                user["id"],
                difficulty,
                word_length,
                exam_date,
                daily_target,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        db.commit()
        for key in ["current_word_id", "guesses", "awaiting_revival", "revival_word_id", "revival_options", "max_attempts", "revived"]:
            session.pop(key, None)
        flash(f"設定完成：每日目標 {daily_target} 個單字。", "success")
        return redirect(url_for("game"))

    today_text = date.today().isoformat()
    return render_template("setup.html", settings=existing, today_text=today_text, word_lengths=WORD_LENGTHS)


@app.route("/game", methods=["GET", "POST"])
def game():
    guard = require_user()
    if guard:
        return guard
    user = current_user()
    settings = user_settings(user["id"])
    if not settings:
        return redirect(url_for("setup"))

    db = get_db()
    if not session.get("current_word_id"):
        word = choose_word(user["id"], settings["difficulty"], settings["word_length"])
        session["current_word_id"] = word["id"]
        session["guesses"] = []
        session["max_attempts"] = 6
        session["revived"] = False

    word = db.execute("SELECT * FROM words WHERE id = ?", (session["current_word_id"],)).fetchone()

    if request.method == "POST" and not session.get("awaiting_revival"):
        guess = request.form.get("guess", "").strip().lower()
        if len(guess) != len(word["word"]) or not guess.isalpha():
            flash(f"請輸入 {len(word['word'])} 個英文字母。", "error")
        elif not is_valid_guess(guess):
            flash("這不是字典裡的有效英文單字，這次不扣嘗試次數。", "error")
        else:
            guesses = session.get("guesses", [])
            guesses.append({"text": guess, "marks": score_guess(word["word"], guess)})
            session["guesses"] = guesses
            session.modified = True
            if guess == word["word"]:
                finalize_wordle(True)
                flash("答對了，這個單字已排入未來複習。", "success")
                return redirect(url_for("stats"))
            if len(guesses) >= session.get("max_attempts", 6):
                if not session.get("revived") and prepare_revival(user["id"]):
                    flash("6 次挑戰用完，復活賽開始。", "info")
                else:
                    answer = word["word"]
                    finalize_wordle(False)
                    flash(f"挑戰結束，答案是 {answer}。", "error")
                    return redirect(url_for("stats"))

    revival_word = None
    if session.get("awaiting_revival"):
        revival_word = db.execute("SELECT * FROM words WHERE id = ?", (session["revival_word_id"],)).fetchone()

    status = today_status(user["id"])
    accuracy, history_count, mistake_count = level_accuracy(user["id"], settings["difficulty"])
    return render_template(
        "game.html",
        word=word,
        guesses=session.get("guesses", []),
        max_attempts=session.get("max_attempts", 6),
        status=status,
        settings=settings,
        days_left=days_until_exam(settings["exam_date"]),
        accuracy=accuracy,
        history_count=history_count,
        mistake_count=mistake_count,
        revival_word=revival_word,
        revival_options=session.get("revival_options", []),
        keyboard_rows=keyboard_rows(session.get("guesses", [])),
    )


@app.post("/revival")
def revival():
    guard = require_user()
    if guard:
        return guard
    if not session.get("awaiting_revival"):
        return redirect(url_for("game"))

    user = current_user()
    db = get_db()
    revival_word = db.execute("SELECT * FROM words WHERE id = ?", (session["revival_word_id"],)).fetchone()
    selected = request.form.get("meaning", "")

    if selected == revival_word["meaning"]:
        remove_mistake(user["id"], revival_word["id"])
        db.commit()
        session["awaiting_revival"] = False
        session["revived"] = True
        session["max_attempts"] = len(session.get("guesses", [])) + 2
        flash("復活成功，額外獲得 2 次 Wordle 機會。", "success")
        return redirect(url_for("game"))

    add_history(user["id"], revival_word["id"], revival_word["level"], False, 1, "revival")
    update_spaced_repetition(user["id"], revival_word["id"], False)
    add_mistake(user["id"], revival_word["id"])
    db.commit()
    answer = db.execute("SELECT word FROM words WHERE id = ?", (session["current_word_id"],)).fetchone()["word"]
    finalize_wordle(False)
    flash(f"復活失敗，當局結束。Wordle 答案是 {answer}。", "error")
    return redirect(url_for("stats"))


@app.route("/stats")
def stats():
    guard = require_user()
    if guard:
        return guard
    user = current_user()
    settings = user_settings(user["id"])
    if not settings:
        return redirect(url_for("setup"))
    status = today_status(user["id"])
    accuracy, history_count, mistake_count = level_accuracy(user["id"], settings["difficulty"])
    return render_template(
        "stats.html",
        status=status,
        settings=settings,
        accuracy=accuracy,
        history_count=history_count,
        mistake_count=mistake_count,
        last_result=session.pop("last_result", None),
    )


@app.route("/mistakes", methods=["GET", "POST"])
def mistakes():
    guard = require_user()
    if guard:
        return guard
    user = current_user()
    db = get_db()

    if request.method == "POST":
        word_id = int(request.form.get("word_id", "0"))
        selected = request.form.get("meaning", "")
        word = db.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
        if word and selected == word["meaning"]:
            remove_mistake(user["id"], word["id"])
            add_history(user["id"], word["id"], word["level"], True, 1, "mistake_drill")
            update_spaced_repetition(user["id"], word["id"], True)
            flash("錯題特訓答對，已從錯題本移除。", "success")
        elif word:
            add_history(user["id"], word["id"], word["level"], False, 1, "mistake_drill")
            update_spaced_repetition(user["id"], word["id"], False)
            add_mistake(user["id"], word["id"])
            flash("這題仍保留在錯題本，之後會再遇到。", "error")
        db.commit()
        return redirect(url_for("mistakes"))

    mistake_rows = db.execute(
        """
        SELECT w.*
        FROM mistakes m
        JOIN words w ON w.id = m.word_id
        WHERE m.user_id = ?
        ORDER BY w.level, w.word
        """,
        (user["id"],),
    ).fetchall()
    drill_word = random.choice(mistake_rows) if mistake_rows else None
    options = build_mcq_options(drill_word) if drill_word else []
    return render_template("mistakes.html", mistakes=mistake_rows, drill_word=drill_word, options=options)


@app.route("/profile")
def profile():
    guard = require_user()
    if guard:
        return guard
    user = current_user()
    db = get_db()
    rows = []
    for level in LEVELS:
        learned = db.execute(
            """
            SELECT COUNT(DISTINCT word_id) AS c
            FROM history
            WHERE user_id = ? AND level = ?
            """,
            (user["id"], level),
        ).fetchone()["c"]
        accuracy, history_count, _mistakes = level_accuracy(user["id"], level)
        rows.append(
            {
                "level": level,
                "progress": min(100, round((learned / LEVEL_TARGETS[level]) * 100)),
                "learned": learned,
                "target": LEVEL_TARGETS[level],
                "accuracy": accuracy,
                "history_count": history_count,
            }
        )
    return render_template("profile.html", user=user, rows=rows, settings=user_settings(user["id"]))


@app.route("/leaderboard")
def leaderboard():
    guard = require_user()
    if guard:
        return guard
    rows = get_db().execute(
        """
        SELECT u.username, u.user_id, COUNT(h.id) AS correct_total
        FROM users u
        LEFT JOIN history h ON h.user_id = u.id AND h.success = 1
        GROUP BY u.id
        ORDER BY correct_total DESC, u.created_at ASC
        LIMIT 10
        """
    ).fetchall()
    return render_template("leaderboard.html", rows=rows)


init_db()


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
