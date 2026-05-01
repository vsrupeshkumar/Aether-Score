/**
 * AETHER-SCORE Embeddable Widget
 * One-click integration script
 */
(function() {
    'use strict';
    
    const defaultConfig = {
        apiUrl: 'https://AETHER-SCORE-backend.onrender.com',
        theme: 'light',
        size: 'medium',
    };
    
    function createWidget(config) {
        const widgetId = 'AETHER-SCORE-widget-' + Math.random().toString(36).substr(2, 9);
        const container = document.getElementById(config.containerId || 'AETHER-SCORE-widget-container');
        
        if (!container) {
            console.error('AETHER-SCORE: Container element not found');
            return;
        }
        
        const iframe = document.createElement('iframe');
        iframe.id = widgetId;
        iframe.src = `${config.widgetUrl || '/widget/index.html'}?address=${encodeURIComponent(config.address)}&apiUrl=${encodeURIComponent(config.apiUrl || defaultConfig.apiUrl)}&apiKey=${encodeURIComponent(config.apiKey || '')}`;
        iframe.style.border = 'none';
        iframe.style.width = config.width || '100%';
        iframe.style.height = config.height || '300px';
        iframe.style.borderRadius = '12px';
        iframe.setAttribute('allowtransparency', 'true');
        
        container.appendChild(iframe);
        
        return {
            destroy: function() {
                iframe.remove();
            }
        };
    }
    
    // Auto-initialize if script has data attributes
    if (document.currentScript) {
        const script = document.currentScript;
        const address = script.getAttribute('data-address');
        const containerId = script.getAttribute('data-container') || 'AETHER-SCORE-widget-container';
        
        if (address) {
            // Create container if it doesn't exist
            let container = document.getElementById(containerId);
            if (!container) {
                container = document.createElement('div');
                container.id = containerId;
                script.parentNode.insertBefore(container, script);
            }
            
            createWidget({
                address: address,
                containerId: containerId,
                apiUrl: script.getAttribute('data-api-url') || defaultConfig.apiUrl,
                apiKey: script.getAttribute('data-api-key') || '',
            });
        }
    }
    
    // Export for manual initialization
    window.AETHER-SCORE = {
        createWidget: createWidget,
    };
})();


