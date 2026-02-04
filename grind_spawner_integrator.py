import task_scheduler
import grind_spawner

def integrate_task_scheduler():
    dependency_graph = task_scheduler.DependencyGraph()
    task_scheduler = task_scheduler.TaskScheduler(dependency_graph)
    # Integrate task scheduler with grind spawner
    # This will require modifying the grind_spawner.py file, which is read-only
    # Instead, we will create a new function in the grind_spawner_integrator.py file
    # that will use the task scheduler to schedule tasks
    def schedule_tasks():
        task_scheduler.schedule_tasks()
    return schedule_tasks

def main():
    schedule_tasks = integrate_task_scheduler()
    schedule_tasks()

if __name__ == '__main__':
    main()