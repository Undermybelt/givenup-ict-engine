use std::collections::HashMap;

use crate::factor_lab::factor_definition::FactorDefinition;

#[derive(Default)]
pub struct FactorRegistry {
    factors: HashMap<String, FactorDefinition>,
}

impl FactorRegistry {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn register(&mut self, factor: FactorDefinition) {
        self.factors.insert(factor.name.clone(), factor);
    }

    pub fn get(&self, name: &str) -> Option<&FactorDefinition> {
        self.factors.get(name)
    }

    pub fn list(&self) -> Vec<&FactorDefinition> {
        self.factors.values().collect()
    }

    pub fn len(&self) -> usize {
        self.factors.len()
    }

    pub fn is_empty(&self) -> bool {
        self.factors.is_empty()
    }
}
