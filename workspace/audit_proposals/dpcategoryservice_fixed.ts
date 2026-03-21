/**
 * RAE Phoenix Shadow Audit Proposal: DpCategoryService
 * Verdict: REJECTED (Tier 2) - Legacy $q detected.
 * Refactored to Silicon Oracle v2.9 Standards.
 */

import { getApi } from '@/lib/api';

// Define Interfaces for strict typing (Advanced Senior Standard)
export interface Category {
    id: number;
    name: string;
    url: string;
    // ... rest of fields
}

export const DpCategoryService = {
    resource: '/categories', // Moved hardcoded strings to scoped constants

    getPublic: async (): Promise<Category[]> => {
        try {
            const data = await getApi(`${DpCategoryService.resource}/forViewPublic/1`);
            return data;
        } catch (error) {
            console.error('[RAE-Quality] Category fetch failed:', error);
            throw error;
        }
    },

    getOneForView: async (categoryUrl: string): Promise<Category> => {
        if (!categoryUrl) throw new Error('Category URL is mandatory');
        
        try {
            const data = await getApi(`${DpCategoryService.resource}/oneForView/${categoryUrl}`);
            return data;
        } catch (error) {
            throw error;
        }
    },

    /**
     * Refactored: Replaced AngularJS $q with native async/await for performance and consistency.
     */
    manyForView: async (categories: string[]): Promise<Category[]> => {
        try {
            const data = await getApi(`${DpCategoryService.resource}/manyForView`, {
                params: { categories: categories.join(',') }
            });
            return data;
        } catch (error) {
            throw error;
        }
    }
};
