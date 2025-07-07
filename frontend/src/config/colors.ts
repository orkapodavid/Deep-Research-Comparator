export const colors = {
    primary: '#112D4E',
    secondary: '#3F72AF',
    light: '#DBE2EF',
    background: '#F9F7F7',
} as const;

// export const colors = {
//     primary: '#27374D',
//     secondary: '#526D82',
//     light: '#9DB2BF',
//     background: '#DDE6ED',
// } as const;

export type ColorKey = keyof typeof colors; 