const API_BASE = "http://127.0.0.1:8001/api";

// Tab Management
function showTab(tabName) {
	// Hide all tab contents
	document.querySelectorAll('.tab-content').forEach(tab => {
		tab.classList.remove('active');
	});
	
	// Remove active class from all tab buttons
	document.querySelectorAll('.tab-btn').forEach(btn => {
		btn.classList.remove('active');
	});
	
	// Show selected tab content
	document.getElementById(`${tabName}-tab`).classList.add('active');
	
	// Add active class to clicked button
	event.target.classList.add('active');
	
	// Load specific tab data
	if (tabName === 'analytics') {
		loadAnalytics();
	}
}

// Original Functions (Enhanced)
function section(titleText) {
	const container = document.createElement("section");
	const h2 = document.createElement("h2");
	h2.textContent = titleText;
	container.appendChild(h2);
	return container;
}

function itemRow(post) {
	const li = document.createElement("li");
	const title = document.createElement("strong");
	title.textContent = post.title || "(no title)";
	li.appendChild(title);
	li.appendChild(document.createElement("br"));
	if (post.description) {
		const desc = document.createElement("span");
		desc.textContent = post.description.length > 200 ? 
			post.description.substring(0, 200) + "..." : post.description;
		desc.style.color = "#666";
		li.appendChild(desc);
		li.appendChild(document.createElement("br"));
	}
	
	// Add category badge
	const categoryBadge = document.createElement("span");
	categoryBadge.textContent = post.category || "Unknown";
	categoryBadge.className = `category-badge ${(post.category || "").toLowerCase()}`;
	categoryBadge.style.cssText = `
		background: #667eea; color: white; padding: 2px 8px; 
		border-radius: 12px; font-size: 0.8rem; margin-right: 10px;
	`;
	li.appendChild(categoryBadge);
	
	if (post.url) {
		const a = document.createElement("a");
		a.href = post.url;
		a.target = "_blank";
		a.textContent = "View Original";
		a.style.cssText = "color: #667eea; text-decoration: none; margin-right: 10px;";
		li.appendChild(a);
	}
	
	const subredditInfo = document.createElement("span");
	subredditInfo.textContent = `r/${post.subreddit || "unknown"}`;
	subredditInfo.style.cssText = "color: #999; font-size: 0.9rem;";
	li.appendChild(subredditInfo);
	
	return li;
}

async function loadGrouped() {
	try {
		showStatus("Loading problems...", "info");
		const res = await fetch(`${API_BASE}/problems_grouped`);
		const data = await res.json();
		const container = document.getElementById("grouped");
		container.innerHTML = "";

		const order = ["Software", "Hardware", "Other"];
		let totalProblems = 0;
		
		order.forEach(cat => {
			const posts = data[cat] || [];
			totalProblems += posts.length;
			const sec = section(`${cat} (${posts.length})`);
			const ul = document.createElement("ul");
			posts.forEach(p => ul.appendChild(itemRow(p)));
			sec.appendChild(ul);
			container.appendChild(sec);
		});
		
		showStatus(`✅ Loaded ${totalProblems} problems successfully`, "success");
	} catch (error) {
		showStatus(`❌ Error loading problems: ${error.message}`, "error");
	}
}

// Enhanced Status Display
function showStatus(message, type = "info") {
	const statusDiv = document.getElementById("status");
	if (statusDiv) {
		statusDiv.textContent = message;
		statusDiv.className = `status-info ${type}`;
		
		// Auto-hide after 5 seconds for success messages
		if (type === "success") {
			setTimeout(() => {
				statusDiv.textContent = "";
				statusDiv.className = "status-info";
			}, 5000);
		}
	}
}

// Real Data Fetching
async function fetchRealData() {
	try {
		showStatus("🚀 Fetching real Reddit data...", "info");
		const res = await fetch(`${API_BASE}/fetch/real-reddit`, { method: 'POST' });
		const data = await res.json();
		
		if (data.status === 'success') {
			showStatus(`✅ Successfully fetched ${data.total_inserted || 0} new problems!`, "success");
			// Reload the problems display
			setTimeout(loadGrouped, 1000);
		} else {
			showStatus(`⚠️ Fetch completed with warnings: ${data.message || 'Unknown issue'}`, "warning");
		}
	} catch (error) {
		showStatus(`❌ Error fetching real data: ${error.message}`, "error");
	}
}

// Search Problems
async function searchProblems() {
	const query = document.getElementById("search-input").value.trim();
	if (!query) {
		alert("Please enter a search term");
		return;
	}
	
	try {
		showStatus(`🔍 Searching for: ${query}`, "info");
		const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
		const data = await res.json();
		
		// Display search results
		const container = document.getElementById("grouped");
		container.innerHTML = "";
		
		const sec = section(`Search Results for "${query}" (${data.length})`);
		const ul = document.createElement("ul");
		data.forEach(p => ul.appendChild(itemRow(p)));
		sec.appendChild(ul);
		container.appendChild(sec);
		
		showStatus(`✅ Found ${data.length} matching problems`, "success");
	} catch (error) {
		showStatus(`❌ Search error: ${error.message}`, "error");
	}
}

// RAG System Functions
async function startRAGPipeline() {
	try {
		showRAGStatus("🚀 Starting comprehensive RAG pipeline...", "info");
		const res = await fetch(`${API_BASE}/rag/start-pipeline`, { method: 'POST' });
		const data = await res.json();
		
		displayRAGResults(data);
		
		if (data.status === 'success') {
			showRAGStatus("✅ RAG pipeline completed successfully!", "success");
		} else {
			showRAGStatus("⚠️ RAG pipeline completed with issues", "warning");
		}
	} catch (error) {
		showRAGStatus(`❌ RAG pipeline error: ${error.message}`, "error");
	}
}

async function getRAGStats() {
	try {
		showRAGStatus("📊 Loading RAG statistics...", "info");
		const res = await fetch(`${API_BASE}/rag/stats`);
		const data = await res.json();
		
		displayRAGStats(data);
		showRAGStatus("✅ RAG stats loaded successfully", "success");
	} catch (error) {
		showRAGStatus(`❌ Error loading RAG stats: ${error.message}`, "error");
	}
}

async function triggerRedditCollection() {
	try {
		showRAGStatus("📡 Triggering Reddit data collection...", "info");
		const res = await fetch(`${API_BASE}/rag/collect-reddit`, { method: 'POST' });
		const data = await res.json();
		
		displayRAGCollectionResult(data);
	} catch (error) {
		showRAGStatus(`❌ Reddit collection error: ${error.message}`, "error");
	}
}

async function triggerSummarization() {
	try {
		showRAGStatus("🧠 Generating problem summaries...", "info");
		const res = await fetch(`${API_BASE}/rag/summarize-problems`, { method: 'POST' });
		const data = await res.json();
		
		displaySummarizationResult(data);
	} catch (error) {
		showRAGStatus(`❌ Summarization error: ${error.message}`, "error");
	}
}

async function analyzeText() {
	const title = document.getElementById("analyze-title").value.trim();
	const description = document.getElementById("analyze-description").value.trim();
	
	if (!title) {
		alert("Please enter a problem title");
		return;
	}
	
	try {
		showRAGStatus("🔍 Analyzing text with NLP...", "info");
		const res = await fetch(`${API_BASE}/rag/analyze-text`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: `title=${encodeURIComponent(title)}&description=${encodeURIComponent(description)}`
		});
		const data = await res.json();
		
		displayTextAnalysis(data);
		showRAGStatus("✅ Text analysis completed", "success");
	} catch (error) {
		showRAGStatus(`❌ Text analysis error: ${error.message}`, "error");
	}
}

async function startContinuousCollection() {
	try {
		showRAGStatus("🔄 Starting continuous data collection...", "info");
		const res = await fetch(`${API_BASE}/rag/continuous-collection/start`, { method: 'POST' });
		const data = await res.json();
		
		if (data.status === 'started') {
			showRAGStatus("✅ Continuous collection started in background", "success");
		}
	} catch (error) {
		showRAGStatus(`❌ Error starting continuous collection: ${error.message}`, "error");
	}
}

// AI Summaries Functions
async function loadRecentSummaries() {
	try {
		const severity = document.getElementById("severity-filter").value;
		const category = document.getElementById("category-filter").value;
		
		let url = `${API_BASE}/rag/recent-summaries?limit=20`;
		if (severity) url += `&severity=${severity}`;
		if (category) url += `&category=${category}`;
		
		const res = await fetch(url);
		const data = await res.json();
		
		displaySummaries(data.summaries);
	} catch (error) {
		console.error("Error loading summaries:", error);
	}
}

// Analytics Functions
async function loadAnalytics() {
	try {
		// Load multiple analytics endpoints
		const [statusRes, ragStatsRes] = await Promise.all([
			fetch(`${API_BASE}/status`),
			fetch(`${API_BASE}/rag/stats`)
		]);
		
		const statusData = await statusRes.json();
		const ragStatsData = await ragStatsRes.json();
		
		displayAnalytics(statusData, ragStatsData);
	} catch (error) {
		console.error("Error loading analytics:", error);
	}
}

// Display Functions
function showRAGStatus(message, type = "info") {
	const resultsDiv = document.getElementById("rag-results");
	const statusElement = document.createElement("div");
	statusElement.className = `message ${type}`;
	statusElement.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
	resultsDiv.insertBefore(statusElement, resultsDiv.firstChild);
	
	// Keep only last 10 messages
	const messages = resultsDiv.querySelectorAll('.message');
	if (messages.length > 10) {
		messages[messages.length - 1].remove();
	}
}

function displayRAGResults(data) {
	const resultsDiv = document.getElementById("rag-results");
	const resultElement = document.createElement("div");
	resultElement.className = "code-block";
	resultElement.innerHTML = `
		<h4>🚀 RAG Pipeline Results</h4>
		<strong>Status:</strong> ${data.status}<br>
		<strong>Timestamp:</strong> ${data.timestamp}<br>
		<strong>Reddit Collection:</strong> ${data.reddit_collection.posts_collected || 0} posts, ${data.reddit_collection.errors || 0} errors<br>
		<strong>X Collection:</strong> ${data.x_collection.status}<br>
		<strong>Summarization:</strong> ${data.summarization.summaries_created || 0} summaries created<br>
		<strong>Message:</strong> ${data.message}
	`;
	resultsDiv.appendChild(resultElement);
}

function displayRAGStats(data) {
	const resultsDiv = document.getElementById("rag-results");
	const statsElement = document.createElement("div");
	statsElement.className = "code-block";
	statsElement.innerHTML = `
		<h4>📊 RAG System Statistics</h4>
		<strong>Total Problems:</strong> ${data.total_problems}<br>
		<strong>Recent (7 days):</strong> ${data.recent_problems_7d}<br>
		<strong>Categories:</strong> ${JSON.stringify(data.category_distribution, null, 2)}<br>
		<strong>RAG Status:</strong> ${data.rag_status}<br>
		<strong>Last Updated:</strong> ${data.last_updated}
	`;
	resultsDiv.appendChild(statsElement);
}

function displayTextAnalysis(data) {
	const resultsDiv = document.getElementById("rag-results");
	const analysisElement = document.createElement("div");
	analysisElement.className = "code-block";
	const analysis = data.analysis;
	
	analysisElement.innerHTML = `
		<h4>🧠 NLP Text Analysis Results</h4>
		<strong>Problem Statement:</strong> ${analysis.problem_statement}<br>
		<strong>Detected Issues:</strong> ${analysis.detected_issues.join(", ") || "None"}<br>
		<strong>Affected Components:</strong> ${analysis.affected_components.join(", ") || "None"}<br>
		<strong>Symptoms:</strong> ${analysis.symptoms.join(", ") || "None"}<br>
		<strong>Severity:</strong> ${analysis.severity}<br>
		<strong>Category Confidence:</strong><br>
		&nbsp;&nbsp;Hardware: ${(analysis.category_confidence.hardware * 100).toFixed(1)}%<br>
		&nbsp;&nbsp;Software: ${(analysis.category_confidence.software * 100).toFixed(1)}%<br>
		&nbsp;&nbsp;Other: ${(analysis.category_confidence.other * 100).toFixed(1)}%<br>
		<strong>Generated At:</strong> ${analysis.generated_at}
	`;
	resultsDiv.appendChild(analysisElement);
}

function displaySummaries(summaries) {
	const container = document.getElementById("summaries-container");
	container.innerHTML = "";
	
	if (!summaries || summaries.length === 0) {
		container.innerHTML = "<p>No summaries found. Try generating some first!</p>";
		return;
	}
	
	summaries.forEach(item => {
		const summary = item.summary;
		const card = document.createElement("div");
		card.className = `summary-card severity-${summary.severity}`;
		
		card.innerHTML = `
			<div class="summary-header">
				<h4>${item.title.substring(0, 60)}${item.title.length > 60 ? "..." : ""}</h4>
				<span class="severity-badge severity-${summary.severity}">${summary.severity}</span>
			</div>
			<p><strong>Problem Statement:</strong> ${summary.problem_statement}</p>
			<p><strong>Category:</strong> ${item.category} | <strong>Source:</strong> r/${item.subreddit}</p>
			<p><strong>Issues:</strong> ${summary.detected_issues.join(", ") || "None detected"}</p>
			<p><strong>Components:</strong> ${summary.affected_components.join(", ") || "None identified"}</p>
			${item.url ? `<a href="${item.url}" target="_blank">View Original Post</a>` : ""}
		`;
		
		container.appendChild(card);
	});
}

function displayAnalytics(statusData, ragStatsData) {
	// Collection Stats
	document.getElementById("collection-stats").innerHTML = `
		<p>Total Problems: <strong>${statusData.total_problems}</strong></p>
		<p>Reddit Posts: <strong>${statusData.sources.reddit}</strong></p>
		<p>X Posts: <strong>${statusData.sources.x}</strong></p>
		<p>Database: <strong>${statusData.database_connected ? "✅ Connected" : "❌ Disconnected"}</strong></p>
	`;
	
	// Category Distribution
	const categories = statusData.categories;
	document.getElementById("category-distribution").innerHTML = `
		<p>Software: <strong>${categories.Software}</strong></p>
		<p>Hardware: <strong>${categories.Hardware}</strong></p>
		<p>Other: <strong>${categories.Other}</strong></p>
	`;
	
	// Source Analysis
	document.getElementById("source-analysis").innerHTML = `
		<p>Most Recent Problems:</p>
		${statusData.latest_problems.map(p => 
			`<small>• ${p.title} (${p.category})</small>`
		).join("<br>")}
	`;
	
	// RAG Performance
	if (ragStatsData && !ragStatsData.error) {
		document.getElementById("rag-performance").innerHTML = `
			<p>RAG Status: <strong>${ragStatsData.rag_status}</strong></p>
			<p>Recent Problems (7d): <strong>${ragStatsData.recent_problems_7d}</strong></p>
			<p>Last Updated: <strong>${new Date(ragStatsData.last_updated).toLocaleString()}</strong></p>
		`;
	} else {
		document.getElementById("rag-performance").innerHTML = `
			<p>RAG Status: <strong>Error loading stats</strong></p>
		`;
	}
}

// Search on Enter key
document.addEventListener("DOMContentLoaded", function() {
	loadGrouped();
	
	const searchInput = document.getElementById("search-input");
	if (searchInput) {
		searchInput.addEventListener("keypress", function(e) {
			if (e.key === "Enter") {
				searchProblems();
			}
		});
	}
});

// Make functions globally available
window.showTab = showTab;
window.fetchRealData = fetchRealData;
window.searchProblems = searchProblems;
window.startRAGPipeline = startRAGPipeline;
window.getRAGStats = getRAGStats;
window.triggerRedditCollection = triggerRedditCollection;
window.triggerSummarization = triggerSummarization;
window.analyzeText = analyzeText;
window.startContinuousCollection = startContinuousCollection;
window.loadRecentSummaries = loadRecentSummaries;
