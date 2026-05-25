import { auth } from '../utils/auth.js';

export function mountLanding(container, onLogin) {
    container.innerHTML = `
        <div id="landing-wrapper" class="min-h-screen w-full flex items-center justify-center overflow-hidden text-ink font-body relative bg-desk">
            <!-- Background Tactical Desk -->
            <div class="absolute inset-0 opacity-50 pointer-events-none z-0" style="background-image: url('./assets/tactical_intelligence_bg.png'); background-size: cover; background-position: center; filter: brightness(0.6) contrast(1.1) blur(1px);"></div>

            <!-- LAYER 1: The Login Desk (Z-index 0) -->
            <div id="login-view" class="absolute inset-0 flex items-center justify-center z-0 opacity-0 transition-opacity duration-[3000ms] ease-in-out">
                <div class="bg-paper p-10 max-w-md w-full mx-4 relative filter drop-shadow-2xl border-4 border-double border-ink">
                    <!-- Corner Accents -->
                    <div class="absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2 border-ink"></div>
                    <div class="absolute top-2 right-2 w-4 h-4 border-t-2 border-r-2 border-ink"></div>
                    <div class="absolute bottom-2 left-2 w-4 h-4 border-b-2 border-l-2 border-ink"></div>
                    <div class="absolute bottom-2 right-2 w-4 h-4 border-b-2 border-r-2 border-ink"></div>

                    <div class="text-center mb-8">
                        <h2 class="text-3xl font-heading font-black uppercase border-b-2 border-ink pb-4 inline-block">Dashboard Login</h2>
                    </div>

                    <div class="pt-6 flex flex-col space-y-4">
                        <button id="loginRouteBtn" class="w-full bg-ink text-paper py-3 font-bold uppercase tracking-widest hover:bg-accent transition-colors duration-300 border-2 border-transparent">
                            USER LOGIN
                        </button>
                        <button id="guestAccessBtn" class="w-full bg-transparent border-2 border-ink text-ink py-3 font-bold uppercase tracking-widest hover:bg-ink hover:text-paper transition-colors duration-300">
                            ENTER AS GUEST
                        </button>
                    </div>
                </div>
            </div>

            <!-- LAYER 2: The Newspaper (Z-index 10) -->
            <div id="newspaper-reveal" class="absolute inset-0 flex items-center justify-center z-10 pointer-events-auto transition-all duration-1000">
                <div class="relative w-[90vw] max-w-[1000px] h-[85vh] flex">
                    <!-- Left Half -->
                    <div class="paper-half left-half w-1/2 h-full overflow-hidden relative bg-paper shadow-[inset_-10px_0_20px_rgba(0,0,0,0.05)] transition-all duration-1000 ease-in-out" id="left-half-container">
                        <div class="content-container absolute top-0 left-0 h-full p-8 box-border" id="left-content"></div>
                    </div>

                    <!-- Right Half -->
                    <div class="paper-half right-half w-1/2 h-full overflow-hidden relative bg-paper shadow-[inset_10px_0_20px_rgba(0,0,0,0.05)] transition-all duration-1000 ease-in-out" id="right-half-container">
                        <div class="content-container absolute top-0 left-0 h-full p-8 box-border" id="right-content"></div>
                    </div>

                    <!-- The Tear Button -->
                    <button id="tear-btn" class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20 
                                                 bg-accent text-paper border-4 border-paper font-mono font-bold tracking-[0.15em] 
                                                 text-base px-8 py-4 uppercase shadow-xl hover:scale-110 transition-all duration-300 whitespace-nowrap">
                        ENTER PORTAL
                    </button>
                </div>
            </div>
        </div>

        <template id="newspaper-template">
            <div class="w-full h-full text-justify text-sm md:text-base text-ink">
                <div style="column-span: all;" class="text-center border-b-4 border-double border-ink mb-6 pb-6">
                    <div class="flex justify-between items-center font-mono text-xs font-bold border-b-2 border-ink pb-2 mb-4">
                        <span>VOL. XLIV... NO. 12</span>
                        <span>MAY 2026</span>
                        <span>PRICE: TWO CENTS</span>
                    </div>
                    <h1 class="text-5xl lg:text-7xl font-heading font-black uppercase tracking-tight leading-none mb-2">GLOBAL NEWS PULSE</h1>
                    <h2 class="text-xl lg:text-2xl font-body font-bold italic opacity-80">Global News Sentiment & Entity Analysis Pipeline</h2>
                    
                    <!-- Decorative Page-Tear SVG -->
                    <div class="page-tear-wrapper mt-4">
                        <svg class="page-tear h-8 w-full fill-ink opacity-20" viewBox="0 0 1000 50" preserveAspectRatio="none">
                            <path d="M0,0 Q10,20 20,0 T40,0 T60,0 T80,0 T100,0 T120,0 T140,0 T160,0 T180,0 T200,0 T220,0 T240,0 T260,0 T280,0 T300,0 T320,0 T340,0 T360,0 T380,0 T400,0 T420,0 T440,0 T460,0 T480,0 T500,0 T520,0 T540,0 T560,0 T580,0 T600,0 T620,0 T640,0 T660,0 T680,0 T700,0 T720,0 T740,0 T760,0 T780,0 T800,0 T820,0 T840,0 T860,0 T880,0 T900,0 T920,0 T940,0 T960,0 T980,0 T1000,0 L1000,50 L0,50 Z" />
                        </svg>
                    </div>
                </div>

                <h3 class="font-heading font-bold text-xl uppercase mb-3 text-center border-b border-ink pb-2">Platform Overview</h3>
                <p class="mb-4 leading-relaxed first-letter:text-5xl first-letter:font-black first-letter:float-left first-letter:mr-2 first-letter:mt-[-4px]">
                    This dashboard provides a centralized overview of global multilingual news. By aggregating articles and processing headlines through NLP models, it extracts key sentiment trends and tracks named entities across several international sources.
                </p>
                <p class="mb-4 leading-relaxed">
                    Use the navigation panel on the left to browse sentiment trends, explore connections in the entity database, view geographic node activity, or generate aggregated reports.
                </p>
            </div>
        </template>

        <style>
            .content-container { width: 200%; column-count: 4; column-gap: 40px; }
            .right-half .content-container { transform: translateX(-50%); }
            
            .paper-half {
                transition: clip-path 0.3s ease-out, transform 3.5s cubic-bezier(0.2, 0.8, 0.2, 1), opacity 3s ease-in;
            }
        </style>
    `;

    // Initialize content
    const templateHTML = container.querySelector('#newspaper-template').innerHTML;
    container.querySelector('#left-content').innerHTML = templateHTML;
    container.querySelector('#right-content').innerHTML = templateHTML;

    // Seam Tear Logic
    const POINTS = 60;
    let leftBase = [], leftTorn = [];
    let rightBase = [], rightTorn = [];

    function generatePaths() {
        leftBase = []; leftTorn = [];
        rightBase = []; rightTorn = [];
        
        // Left Seam
        leftBase.push('0% 0%'); leftTorn.push('0% 0%');
        for(let i = 0; i <= POINTS; i++) {
            let y = (i / POINTS) * 100;
            leftBase.push(`100% ${y}%`);
            let tearDepth = 100 - (Math.random() * 6);
            if (i === 0 || i === POINTS) tearDepth = 100;
            leftTorn.push(`${tearDepth}% ${y}%`);
        }
        leftBase.push('0% 100%'); leftTorn.push('0% 100%');

        // Right Seam
        rightBase.push('100% 0%'); rightTorn.push('100% 0%');
        rightBase.push('100% 100%'); rightTorn.push('100% 100%');
        for(let i = POINTS; i >= 0; i--) {
            let y = (i / POINTS) * 100;
            rightBase.push(`0% ${y}%`);
            let tearDepth = Math.random() * 6;
            if (i === 0 || i === POINTS) tearDepth = 0;
            rightTorn.push(`${tearDepth}% ${y}%`);
        }

        const leftHalf = container.querySelector('#left-half-container');
        const rightHalf = container.querySelector('#right-half-container');
        leftHalf.style.clipPath = `polygon(${leftBase.join(', ')})`;
        rightHalf.style.clipPath = `polygon(${rightBase.join(', ')})`;

        return { leftTorn, rightTorn, leftBase, rightBase };
    }

    const paths = generatePaths();

    const tearBtn = container.querySelector('#tear-btn');
    const leftHalf = container.querySelector('#left-half-container');
    const rightHalf = container.querySelector('#right-half-container');
    const revealWrapper = container.querySelector('#newspaper-reveal');

    tearBtn.addEventListener('mouseenter', () => {
        leftHalf.style.clipPath = `polygon(${paths.leftTorn.join(', ')})`;
        rightHalf.style.clipPath = `polygon(${paths.rightTorn.join(', ')})`;
    });

    tearBtn.addEventListener('mouseleave', () => {
        leftHalf.style.clipPath = `polygon(${paths.leftBase.join(', ')})`;
        rightHalf.style.clipPath = `polygon(${paths.rightBase.join(', ')})`;
    });

    tearBtn.addEventListener('click', () => {
        leftHalf.style.clipPath = `polygon(${paths.leftTorn.join(', ')})`;
        rightHalf.style.clipPath = `polygon(${paths.rightTorn.join(', ')})`;
        
        leftHalf.style.transform = 'translateX(-70vw) translateY(10vh) rotate(-15deg)';
        leftHalf.style.opacity = '0';
        leftHalf.style.transition = 'transform 3.5s cubic-bezier(0.2, 0.8, 0.2, 1), opacity 3s ease-in';
        
        rightHalf.style.transform = 'translateX(70vw) translateY(10vh) rotate(15deg)';
        rightHalf.style.opacity = '0';
        rightHalf.style.transition = 'transform 3.5s cubic-bezier(0.2, 0.8, 0.2, 1), opacity 3s ease-in';

        tearBtn.style.opacity = '0';
        tearBtn.style.transform = 'translate(-50%, -50%) scale(0.8)';
        tearBtn.style.transition = 'all 1s ease-out';
        tearBtn.style.pointerEvents = 'none';

        // Reveal the login desk beneath
        const loginView = container.querySelector('#login-view');
        if (loginView) loginView.style.opacity = '1';

        setTimeout(() => {
            revealWrapper.style.display = 'none';
        }, 3500);
    });

    // Actions
    container.querySelector('#loginRouteBtn').addEventListener('click', () => {
        window.location.hash = '#login';
    });

    container.querySelector('#guestAccessBtn').addEventListener('click', async () => {
        try {
            await auth.guest();
            onLogin();
        } catch (err) {
            console.error('Guest access failed:', err);
        }
    });
}

export function unmountLanding() {
    // Optional: remove tailwind script if needed, but usually fine to keep
}
