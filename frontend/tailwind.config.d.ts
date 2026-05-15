declare const _default: {
    darkMode: ["class"];
    content: string[];
    theme: {
        extend: {
            colors: {
                bg: string;
                panel: string;
                elevated: string;
                line: string;
                text: string;
                muted: string;
                accent: {
                    cyan: string;
                    amber: string;
                    lime: string;
                    orange: string;
                    rose: string;
                    sky: string;
                };
            };
            fontFamily: {
                sans: [string, string, string];
                mono: [string, string, string];
            };
            boxShadow: {
                panel: string;
            };
            keyframes: {
                float: {
                    "0%, 100%": {
                        transform: string;
                    };
                    "50%": {
                        transform: string;
                    };
                };
                pulseSoft: {
                    "0%, 100%": {
                        opacity: string;
                        transform: string;
                    };
                    "50%": {
                        opacity: string;
                        transform: string;
                    };
                };
                scan: {
                    "0%": {
                        transform: string;
                    };
                    "100%": {
                        transform: string;
                    };
                };
            };
            animation: {
                float: string;
                pulseSoft: string;
                scan: string;
            };
        };
    };
    plugins: any[];
};
export default _default;
