"""
Sistema de Gerações para Machine Learning
Gerencia diferentes versões do modelo ML para aprendizado contínuo
"""
import os
import json
import time
import shutil
from typing import Dict, List, Optional, Tuple
from loguru import logger
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib


class GenerationManager:
    def __init__(self, base_path="ml_generations"):
        self.base_path = base_path
        self.generations_file = os.path.join(base_path, "generations.json")
        self.current_generation = 0
        self.generations_info = {}
        
        # Criar diretório se não existir
        os.makedirs(base_path, exist_ok=True)
        
        # Carregar informações das gerações existentes
        self._load_generations_info()
        
        # Configurações de evolução
        self.evolution_config = {
            'min_games_for_evolution': 10,  # Mínimo de jogos para evoluir
            'min_win_rate_improvement': 0.05,  # Melhoria mínima de 5% na taxa de vitória
            'max_generations_to_keep': 5,  # Manter apenas as últimas 5 gerações
            'performance_threshold': 0.6,  # Taxa de vitória mínima para considerar boa
            'evolution_patience': 3,  # Tentativas antes de forçar evolução
        }
    
    def _load_generations_info(self):
        """Carrega informações das gerações existentes"""
        try:
            if os.path.exists(self.generations_file):
                with open(self.generations_file, 'r') as f:
                    data = json.load(f)
                    self.current_generation = data.get('current_generation', 0)
                    self.generations_info = data.get('generations', {})
                logger.info(f"Loaded {len(self.generations_info)} generations")
            else:
                self._save_generations_info()
        except Exception as e:
            logger.error(f"Error loading generations info: {e}")
            self.generations_info = {}
    
    def _save_generations_info(self):
        """Salva informações das gerações"""
        try:
            data = {
                'current_generation': self.current_generation,
                'generations': self.generations_info,
                'last_updated': time.time()
            }
            with open(self.generations_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"💾 Generations info saved to {self.generations_file}")
            logger.info(f"   • Current generation: {self.current_generation}")
            logger.info(f"   • Total generations: {len(self.generations_info)}")
        except Exception as e:
            logger.error(f"Error saving generations info: {e}")
    
    def create_new_generation(self, model, scaler, performance_metrics: Dict) -> int:
        """Cria uma nova geração do modelo"""
        try:
            # Incrementar número da geração
            self.current_generation += 1
            generation_id = self.current_generation
            
            # Criar diretório da geração
            generation_path = os.path.join(self.base_path, f"generation_{generation_id}")
            os.makedirs(generation_path, exist_ok=True)
            
            # Salvar modelo e scaler
            model_path = os.path.join(generation_path, "model.pkl")
            model_data = {
                'model': model,
                'scaler': scaler,
                'trained': True,
                'generation_id': generation_id
            }
            joblib.dump(model_data, model_path)
            
            # Salvar métricas de performance
            metrics_path = os.path.join(generation_path, "metrics.json")
            metrics_data = {
                'generation_id': generation_id,
                'created_at': time.time(),
                'performance': performance_metrics,
                'model_info': {
                    'type': 'RandomForestRegressor',
                    'n_estimators': model.n_estimators,
                    'max_depth': model.max_depth
                }
            }
            with open(metrics_path, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            # Atualizar informações das gerações
            self.generations_info[str(generation_id)] = {
                'path': generation_path,
                'created_at': time.time(),
                'performance': performance_metrics,
                'model_path': model_path,
                'metrics_path': metrics_path
            }
            
            # Limpar gerações antigas
            self._cleanup_old_generations()
            
            # Salvar informações atualizadas
            self._save_generations_info()
            
            logger.info(f"🎯 Created new generation {generation_id}")
            logger.info(f"   • Performance: {performance_metrics}")
            logger.info(f"   • Model saved to: {model_path}")
            logger.info(f"   • Metrics saved to: {metrics_path}")
            return generation_id
            
        except Exception as e:
            logger.error(f"Error creating new generation: {e}")
            return 0
    
    def load_best_generation(self) -> Tuple[Optional[RandomForestRegressor], Optional[StandardScaler], Dict]:
        """Carrega a melhor geração baseada na performance"""
        try:
            if not self.generations_info:
                logger.info("No generations available")
                return None, None, {}
            
            # Encontrar a melhor geração baseada na taxa de vitória
            best_generation = None
            best_win_rate = -1
            
            for gen_id, gen_info in self.generations_info.items():
                performance = gen_info.get('performance', {})
                win_rate = performance.get('win_rate', 0)
                
                if win_rate > best_win_rate:
                    best_win_rate = win_rate
                    best_generation = gen_id
            
            if best_generation:
                model_path = self.generations_info[best_generation]['model_path']
                if os.path.exists(model_path):
                    data = joblib.load(model_path)
                    model = data['model']
                    scaler = data['scaler']
                    
                    logger.info(f"Loaded best generation {best_generation} with win rate: {best_win_rate:.2%}")
                    return model, scaler, self.generations_info[best_generation]
            
            logger.warning("No valid generation found")
            return None, None, {}
            
        except Exception as e:
            logger.error(f"Error loading best generation: {e}")
            return None, None, {}
    
    def should_evolve(self, current_performance: Dict, games_played: int) -> bool:
        """Decide se deve evoluir para uma nova geração"""
        try:
            # Verificar se tem jogos suficientes
            if games_played < self.evolution_config['min_games_for_evolution']:
                return False
            
            # Se não há gerações anteriores, evoluir
            if not self.generations_info:
                return True
            
            # Encontrar a melhor performance anterior
            best_previous_win_rate = 0
            for gen_info in self.generations_info.values():
                performance = gen_info.get('performance', {})
                win_rate = performance.get('win_rate', 0)
                best_previous_win_rate = max(best_previous_win_rate, win_rate)
            
            current_win_rate = current_performance.get('win_rate', 0)
            
            # Verificar se há melhoria significativa
            improvement = current_win_rate - best_previous_win_rate
            
            # Critérios para evolução:
            # 1. Melhoria significativa na taxa de vitória
            if improvement >= self.evolution_config['min_win_rate_improvement']:
                logger.info(f"Evolution triggered: {improvement:.2%} improvement in win rate")
                return True
            
            # 2. Performance muito baixa (forçar evolução)
            if current_win_rate < 0.3:
                logger.info(f"Evolution triggered: Low performance ({current_win_rate:.2%})")
                return True
            
            # 3. Muitas tentativas sem evolução (forçar)
            if games_played > 50 and improvement < 0.01:
                logger.info("Evolution triggered: Too many games without improvement")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in evolution decision: {e}")
            return False
    
    def get_generation_statistics(self) -> Dict:
        """Retorna estatísticas de todas as gerações"""
        try:
            stats = {
                'total_generations': len(self.generations_info),
                'current_generation': self.current_generation,
                'generations': {}
            }
            
            for gen_id, gen_info in self.generations_info.items():
                performance = gen_info.get('performance', {})
                stats['generations'][gen_id] = {
                    'win_rate': performance.get('win_rate', 0),
                    'games_played': performance.get('games_played', 0),
                    'created_at': gen_info.get('created_at', 0),
                    'avg_score': performance.get('avg_score', 0),
                    'best_score': performance.get('best_score', 0)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting generation statistics: {e}")
            return {}
    
    def _cleanup_old_generations(self):
        """Remove gerações antigas para economizar espaço"""
        try:
            if len(self.generations_info) <= self.evolution_config['max_generations_to_keep']:
                return
            
            # Ordenar gerações por performance (pior primeiro)
            sorted_generations = sorted(
                self.generations_info.items(),
                key=lambda x: x[1].get('performance', {}).get('win_rate', 0)
            )
            
            # Remover as piores gerações
            generations_to_remove = len(sorted_generations) - self.evolution_config['max_generations_to_keep']
            
            for i in range(generations_to_remove):
                gen_id, gen_info = sorted_generations[i]
                generation_path = gen_info['path']
                
                # Remover diretório da geração
                if os.path.exists(generation_path):
                    shutil.rmtree(generation_path)
                
                # Remover da lista
                del self.generations_info[gen_id]
                
                logger.info(f"Removed old generation {gen_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up old generations: {e}")
    
    def get_evolution_recommendations(self, current_performance: Dict) -> List[str]:
        """Retorna recomendações para evolução"""
        recommendations = []
        
        try:
            current_win_rate = current_performance.get('win_rate', 0)
            games_played = current_performance.get('games_played', 0)
            
            if games_played < self.evolution_config['min_games_for_evolution']:
                recommendations.append(f"Play more games ({games_played}/{self.evolution_config['min_games_for_evolution']})")
            
            if current_win_rate < 0.4:
                recommendations.append("Performance muito baixa - considere ajustar estratégias")
            
            if current_win_rate > 0.7:
                recommendations.append("Performance excelente - mantenha a estratégia atual")
            
            # Comparar com gerações anteriores
            if self.generations_info:
                best_previous = max(
                    gen_info.get('performance', {}).get('win_rate', 0)
                    for gen_info in self.generations_info.values()
                )
                
                if current_win_rate > best_previous:
                    recommendations.append(f"Melhoria de {(current_win_rate - best_previous):.2%} sobre a melhor geração")
                elif current_win_rate < best_previous:
                    recommendations.append(f"Regressão de {(best_previous - current_win_rate):.2%} em relação à melhor geração")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting evolution recommendations: {e}")
            return ["Erro ao analisar recomendações"]
    
    def export_generation_report(self, output_path: str = "generation_report.json"):
        """Exporta relatório completo das gerações"""
        try:
            report = {
                'exported_at': time.time(),
                'total_generations': len(self.generations_info),
                'current_generation': self.current_generation,
                'evolution_config': self.evolution_config,
                'generations': self.generations_info,
                'statistics': self.get_generation_statistics()
            }
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Generation report exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting generation report: {e}")
