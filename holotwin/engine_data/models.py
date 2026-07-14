from django.db import models

class EngineCycleRecord(models.Model):
    engine_id = models.IntegerField()
    cycle = models.IntegerField()
    altitude_m = models.FloatField()
    mach = models.FloatField()
    tamb_k = models.FloatField()
    pamb_pa = models.FloatField()
    rpm_rev_min = models.FloatField()
    fuel_flow_kg_s = models.FloatField()
    p2_pa = models.FloatField()
    t2_k = models.FloatField()
    p3_pa = models.FloatField()
    t3_k = models.FloatField()
    p4_pa = models.FloatField()
    t4_k = models.FloatField()
    compressor_health = models.FloatField()
    combustor_health = models.FloatField()
    turbine_health = models.FloatField()
    overall_health = models.FloatField()
    thrust_n = models.FloatField()
    tsfc_g_n_s = models.FloatField()

    class Meta:
        unique_together = ('engine_id', 'cycle')
        ordering = ['engine_id', 'cycle']

    def __str__(self):
        return f"Engine {self.engine_id} - Cycle {self.cycle}"
