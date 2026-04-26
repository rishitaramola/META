document.addEventListener('DOMContentLoaded', async () => {
    const listEl = document.getElementById('escalated-list');
    const countEl = document.getElementById('pending-count');

    // Modal elements
    const modal = document.getElementById('review-modal');
    const modalCaseId = document.getElementById('modal-case-id');
    const modalComments = document.getElementById('judge-comments');
    const btnCancel = document.getElementById('modal-cancel-btn');
    const btnSubmit = document.getElementById('modal-submit-btn');

    let currentReviewingCaseId = null;

    btnCancel.addEventListener('click', () => {
        modal.style.display = 'none';
        modalComments.value = '';
        currentReviewingCaseId = null;
    });

    btnSubmit.addEventListener('click', () => {
        if (!modalComments.value.trim()) {
            alert('Please add a comment before submitting.');
            return;
        }
        
        // Mock submission to backend
        console.log(\`Submitting review for \${currentReviewingCaseId}: \${modalComments.value}\`);
        
        // Remove from UI
        const card = document.getElementById(\`case-card-\${currentReviewingCaseId}\`);
        if (card) {
            card.remove();
        }
        
        // Update count
        const currentCount = parseInt(countEl.textContent, 10);
        if (currentCount > 0) {
            countEl.textContent = currentCount - 1;
        }

        if (countEl.textContent === '0') {
            listEl.innerHTML = '<div class="text-block" style="text-align:center;">No escalated cases pending. JusticeEngine-01 is handling the load efficiently!</div>';
        }

        modal.style.display = 'none';
        modalComments.value = '';
        
        // Save to localStorage just for demo persistence if needed, though UI removal is enough for the session
        let reviewed = JSON.parse(localStorage.getItem('reviewed_cases') || '[]');
        reviewed.push(currentReviewingCaseId);
        localStorage.setItem('reviewed_cases', JSON.stringify(reviewed));
        
        alert('Review submitted successfully. Case closed.');
    });

    window.openReviewModal = (caseId) => {
        currentReviewingCaseId = caseId;
        modalCaseId.textContent = caseId;
        modal.style.display = 'flex';
    };

    try {
        const res = await fetch('/api/escalated-cases');
        const data = await res.json();
        const cases = data.cases;
        
        // Filter out cases already reviewed in this session
        const reviewed = JSON.parse(localStorage.getItem('reviewed_cases') || '[]');
        const pendingCases = cases.filter(c => !reviewed.includes(c.case_id));

        countEl.textContent = pendingCases.length;

        if (pendingCases.length === 0) {
            listEl.innerHTML = '<div class="text-block" style="text-align:center;">No escalated cases pending. JusticeEngine-01 is handling the load efficiently!</div>';
            return;
        }

        listEl.innerHTML = '';
        pendingCases.reverse().forEach((c, index) => {
            const card = document.createElement('div');
            card.className = 'escalated-card';
            
            // Format reasons
            const reasonsHtml = c.reasons.map(r => `<li>${r}</li>`).join('');

            card.id = \`case-card-\${c.case_id}\`;
            card.innerHTML = \`
                <h3>
                    <span>Case ID: \${c.case_id}</span>
                    <button class="btn primary-btn" style="padding: 0.3rem 0.8rem; font-size:0.85rem;" onclick="window.openReviewModal('\${c.case_id}')">Start Review</button>
                </h3>
                
                <div class="escalation-reason">
                    <strong>User Escalation Reasons:</strong>
                    <ul style="margin-top:0.5rem; margin-left:1.5rem;">
                        ${reasonsHtml}
                    </ul>
                </div>

                <div class="grid-2">
                    <div class="case-summary">
                        <strong style="color:var(--accent-primary)">Case Fact Summary</strong>
                        <p class="mt-3 text-block" style="font-size:0.9rem;">${c.fact_pattern}</p>
                    </div>
                    
                    <div class="ai-summary">
                        <strong style="color:#7289da;">JusticeEngine-01 Preliminary Output</strong>
                        <div style="margin-top:1rem;">
                            <strong>Draft Verdict:</strong> <span class="badge" style="background:rgba(255,255,255,0.1)">${c.ai_verdict}</span>
                        </div>
                        <p class="mt-3 text-block" style="font-size:0.9rem; border-left:2px solid #7289da; padding-left:1rem;">
                            ${c.ai_reasoning}
                        </p>
                    </div>
                </div>
            `;
            listEl.appendChild(card);
        });

    } catch (e) {
        listEl.innerHTML = '<div class="text-block" style="color:var(--accent-danger)">Failed to load escalated cases.</div>';
        console.error(e);
    }
});
