import { Link } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, Map as MapIcon, Cloud, Cpu, Activity, AlertTriangle, CloudRain, Droplets } from 'lucide-react';

export default function LandingPage() {
  const shouldReduceMotion = useReducedMotion();

  // Awwwards-inspired "Living Farm Boundary" animation
  const boundaryVariants = {
    hidden: { pathLength: 0, fillOpacity: 0 },
    visible: { 
      pathLength: 1, 
      fillOpacity: 0.1,
      transition: { 
        pathLength: { duration: shouldReduceMotion ? 0 : 2 },
        fillOpacity: { duration: shouldReduceMotion ? 0 : 1, delay: shouldReduceMotion ? 0 : 1.5 }
      }
    }
  };

  const dataPointVariants = {
    hidden: { opacity: 0, scale: 0.5, y: 20 },
    visible: (custom: number) => ({
      opacity: 1,
      scale: 1,
      y: 0,
      transition: { delay: custom, duration: 0.8 }
    })
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1, 
      transition: { staggerChildren: 0.15, delayChildren: 0.2 } 
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
  };

  return (
    <div className="bg-farm-dark text-white min-h-screen overflow-hidden selection:bg-farm-DEFAULT selection:text-white">
      {/* Hero Section */}
      <section className="relative min-h-[90vh] flex items-center pt-20">
        <div className="absolute inset-0 opacity-10 pointer-events-none">
          {/* Subtle topographic / grid texture could go here, simulating a grid */}
          <div className="w-full h-full" style={{ backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
        </div>

        <div className="container mx-auto px-6 relative z-10 grid lg:grid-cols-2 gap-16 items-center">
          <motion.div 
            initial="hidden"
            animate="visible"
            variants={containerVariants}
            className="max-w-2xl"
          >
            <motion.h1 variants={itemVariants} className="text-5xl md:text-7xl font-bold leading-[1.1] tracking-tight mb-8">
              See the problem.<br />
              <span className="text-farm-light opacity-90">Understand why.</span><br />
              <span className="text-farm-DEFAULT opacity-80">Know what to do.</span>
            </motion.h1>
            
            <motion.p variants={itemVariants} className="text-xl md:text-2xl text-gray-300 font-light leading-relaxed mb-12 max-w-xl">
              FarmSight AI turns satellite, weather, and agricultural data into an explainable Digital Farm Twin for your farm.
            </motion.p>
            
            <motion.div variants={itemVariants} className="flex flex-wrap items-center gap-6">
              <Link to="/login" className="bg-farm-DEFAULT hover:bg-farm-secondary text-white px-8 py-4 rounded-full font-medium text-lg transition-all hover:scale-105 active:scale-95 shadow-xl shadow-farm-DEFAULT/20 flex items-center gap-2">
                Explore your farm <ArrowRight size={20} />
              </Link>
              <a href="#how-it-works" className="text-gray-300 hover:text-white font-medium text-lg px-4 py-2 transition-colors">
                How it works
              </a>
            </motion.div>
          </motion.div>

          <div className="relative h-[500px] w-full hidden lg:flex items-center justify-center">
            {/* Animated SVG Farm Polygon */}
            <svg viewBox="0 0 400 400" className="w-full h-full max-w-md drop-shadow-2xl overflow-visible">
              <motion.path
                d="M 100 50 L 300 80 L 350 250 L 150 350 L 50 200 Z"
                fill="#4caf50"
                stroke="#4caf50"
                strokeWidth="2"
                variants={boundaryVariants}
                initial="hidden"
                animate="visible"
                className="opacity-80"
              />
              
              {/* Converging Data Points */}
              <motion.g custom={2.5} variants={dataPointVariants} initial="hidden" animate="visible">
                <circle cx="80" cy="80" r="4" fill="#ffffff" />
                <text x="95" y="85" fill="#ffffff" className="text-xs font-semibold tracking-widest opacity-80" style={{fontFamily: 'sans-serif'}}>SATELLITE</text>
              </motion.g>
              
              <motion.g custom={2.7} variants={dataPointVariants} initial="hidden" animate="visible">
                <circle cx="320" cy="150" r="4" fill="#ffffff" />
                <text x="335" y="155" fill="#ffffff" className="text-xs font-semibold tracking-widest opacity-80" style={{fontFamily: 'sans-serif'}}>WEATHER</text>
              </motion.g>
              
              <motion.g custom={2.9} variants={dataPointVariants} initial="hidden" animate="visible">
                <circle cx="150" cy="300" r="4" fill="#ffffff" />
                <text x="165" y="305" fill="#ffffff" className="text-xs font-semibold tracking-widest opacity-80" style={{fontFamily: 'sans-serif'}}>FIELD DATA</text>
              </motion.g>

              {/* Center converging target */}
              <motion.g custom={3.5} variants={dataPointVariants} initial="hidden" animate="visible">
                <circle cx="190" cy="195" r="3" fill="#ffffff" />
                <text x="150" y="180" fill="#ffffff" className="text-[10px] font-bold tracking-widest opacity-90" style={{fontFamily: 'sans-serif'}}>FARMSIGHT AI</text>
              </motion.g>
            </svg>
          </div>
        </div>
      </section>

      {/* Story Section 1 */}
      <section id="how-it-works" className="py-32 bg-white text-gray-900">
        <div className="container mx-auto px-6">
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.7 }}
            className="text-center max-w-3xl mx-auto mb-20"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight">One farm. Many signals.</h2>
            <p className="text-xl text-gray-600 leading-relaxed">
              We fuse diverse datasets into a single cohesive map, so you can stop guessing and start understanding exactly what's happening on the ground.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              { icon: MapIcon, title: 'Satellite', desc: 'High-res Sentinel-2 imagery monitoring vegetation.' },
              { icon: CloudRain, title: 'Weather', desc: 'Hyper-local precipitation and temperature from Open-Meteo.' },
              { icon: Droplets, title: 'Soil Moisture', desc: 'Root-zone moisture modeled from ERA5-Land.' },
              { icon: Activity, title: 'Historical', desc: 'Contextual baselines establishing normative farm behavior.' }
            ].map((item, idx) => (
              <motion.div 
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                className="bg-surface p-8 rounded-2xl border border-gray-100 hover:shadow-lg transition-shadow duration-300"
              >
                <div className="w-12 h-12 bg-farm-light rounded-xl flex items-center justify-center mb-6 text-farm-DEFAULT">
                  <item.icon size={24} />
                </div>
                <h3 className="text-xl font-bold mb-3">{item.title}</h3>
                <p className="text-gray-600 leading-relaxed">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Story Section 2 */}
      <section className="py-32 bg-surface">
        <div className="container mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div 
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7 }}
            >
              <h2 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight">Not just a warning.</h2>
              <p className="text-xl text-gray-600 leading-relaxed mb-8">
                When FarmSight AI flags a zone, it explains <strong>why</strong> using SHAP AI explainability, and tells you <strong>what to check</strong> next.
              </p>
              
              <div className="space-y-4">
                <div className="flex items-start gap-4 p-4 rounded-xl bg-white border border-gray-100 shadow-sm">
                  <AlertTriangle className="text-orange-500 mt-1 shrink-0" />
                  <div>
                    <h4 className="font-bold text-gray-900">Moderate Risk</h4>
                    <p className="text-gray-600 text-sm">Water-stress indicators detected.</p>
                  </div>
                </div>
                <div className="flex items-start gap-4 p-4 rounded-xl bg-white border border-gray-100 shadow-sm">
                  <Cpu className="text-farm-DEFAULT mt-1 shrink-0" />
                  <div>
                    <h4 className="font-bold text-gray-900">Why?</h4>
                    <p className="text-gray-600 text-sm">Declining vegetation index and low 30-day rainfall.</p>
                  </div>
                </div>
              </div>
            </motion.div>
            
            <motion.div 
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7 }}
              className="bg-gray-100 rounded-3xl h-[400px] flex items-center justify-center relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-farm-light/30 to-transparent" />
              <div className="relative text-center">
                <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center mx-auto mb-6 shadow-xl text-farm-DEFAULT">
                  <MapIcon size={40} />
                </div>
                <h3 className="text-2xl font-bold text-gray-900">From pixels to zones.</h3>
              </div>
            </motion.div>
          </div>
        </div>
      </section>
      
      {/* Story Section 3 */}
      <section className="py-32 bg-gray-900 text-white text-center">
        <div className="container mx-auto px-6">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="max-w-3xl mx-auto"
          >
            <Cloud className="w-16 h-16 mx-auto mb-8 text-gray-400" />
            <h2 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight">Built for uncertainty.</h2>
            <p className="text-xl text-gray-400 leading-relaxed mb-12">
              Agricultural data is rarely perfect. Cloud cover blocks satellites, and weather stations go offline. FarmSight AI clearly labels missing or stale data, adjusting its confidence so you're never acting on false assumptions.
            </p>
            
            <Link to="/login" className="inline-flex bg-farm-DEFAULT hover:bg-farm-secondary text-white px-8 py-4 rounded-full font-medium text-lg transition-all hover:scale-105 active:scale-95 shadow-xl shadow-farm-DEFAULT/20 items-center gap-2">
              Open your Digital Farm Twin <ArrowRight size={20} />
            </Link>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
