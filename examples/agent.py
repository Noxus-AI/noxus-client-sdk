import os
import sys
from noxus_sdk.client import Client
from noxus_sdk.resources.assistants import TriggerData, TriggerType
from rich.table import Table
from rich.console import Console
from rich.prompt import IntPrompt, Prompt
from rich import box
from httpx import HTTPStatusError

console = Console()
c = Client(os.environ["NOXUS_API_KEY"])
agents = c.agents.list()

# Display agents table
table = Table(box=box.ROUNDED)
table.add_column("#", style="cyan")
table.add_column("ID")
table.add_column("Name", style="green")
table.add_column("Model", style="yellow")
table.add_column("Instructions")
table.add_column("Triggers", style="magenta")

for i, agent in enumerate(agents, 1):
    table.add_row(
        str(i),
        agent.id,
        agent.name,
        agent.definition.model[0] if agent.definition.model else "",
        agent.definition.extra_instructions,
        "\n".join([trigger.definition["type"] for trigger in agent.triggers()]),
    )

console.print(table)

delete_choice = IntPrompt.ask(
    "\n[bold cyan]Select an agent to delete a trigger from[/bold cyan] (enter the number, or 0 to exit)",
    console=console,
    choices=[str(i) for i in range(len(agents) + 1)],
    show_choices=False,
)
if delete_choice != 0:
    selected_agent = agents[delete_choice - 1]
    for trigger in selected_agent.triggers():
        trigger.delete()
        console.print(f"[green]Deleted trigger[/green]: {trigger.definition['type']}")


try:
    choice = IntPrompt.ask(
        "\n[bold cyan]Select an agent to add a trigger to[/bold cyan] (enter the number, or 0 to exit)",
        console=console,
        choices=[str(i) for i in range(len(agents) + 1)],
        show_choices=False,
    )

    if choice == 0:
        console.print("[yellow]Exiting...[/yellow]")
        sys.exit(0)

    selected_agent = agents[choice - 1]
    console.print(
        f"\n[green]Selected agent:[/green] {selected_agent.name} ({selected_agent.id})"
    )

    trigger_type = Prompt.ask("Enter trigger type", choices=["slack", "teams"])
    team_id = Prompt.ask(
        "Enter team ID",
    )
    channel = Prompt.ask(
        "Enter channel",
    )
    keyword = Prompt.ask("Enter keyword", default="")
    selected_agent.add_trigger(
        TriggerData(
            trigger_type=TriggerType(trigger_type),
            team_id=team_id,
            channel=channel or None,
            keyword=keyword or None,
        )
    )

except HTTPStatusError as e:
    console.print(f"\n[red]Error: {e.response.text}[/red]")
except KeyboardInterrupt:
    console.print("\n[yellow]Operation cancelled by user[/yellow]")
    sys.exit(0)
